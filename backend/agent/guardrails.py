"""
Guardrails - 输入侧安全审查、偏离业务过滤与情绪意图分析
提供三层防护体系中的「输入侧安全防护」与「情绪感知共情增强」
结合 L1 确定性规则过滤与 L2 语义向量空间距离判定（解决枚举局限性）
"""
import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import httpx
import numpy as np

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
HR_SEMANTIC_THRESHOLD = float(os.getenv("HR_SEMANTIC_THRESHOLD", "0.40"))

# HR 业务核心领域语义锚点集（用于计算长尾偏离话题的语义空间余弦距离）
HR_DOMAIN_ANCHORS = [
    "员工年假、事假、带薪病假、婚假、产假、育儿假与调休额度查询及休假申请办理",
    "差旅出差审批、差标标准、城市级别住宿餐补与差旅费用报销规范",
    "员工在职证明、收入证明开具、人事档案与印章盖章申请",
    "考勤打卡异常、漏打卡补签、加班工时核算与工资考勤扣减申诉",
    "社保公积金缴纳、医保报销、跨城市公积金转移与员工福利待遇",
    "员工入职办理、试用期转正考核、内部转岗调动、离职交接流程",
    "企业规章制度、报销流程、审批流进度与HR服务工单支持",
]

_ANCHOR_MATRIX: Optional[np.ndarray] = None
_ANCHOR_INIT_FAILED: bool = False


def _get_embedding(text: str, timeout: float = 5.0) -> Optional[np.ndarray]:
    """通过本地 Ollama 获取文本的 BGE-M3 向量并进行 L2 归一化"""
    try:
        url = f"{OLLAMA_URL}/api/embeddings"
        with httpx.Client(timeout=timeout, trust_env=False) as client:
            resp = client.post(url, json={"model": EMBEDDING_MODEL, "prompt": text})
            if resp.status_code == 200:
                raw_emb = resp.json().get("embedding")
                if raw_emb:
                    arr = np.array(raw_emb, dtype=np.float32)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        return arr / norm
    except Exception as e:
        logger.debug(f"[Guardrails] Embedding request skipped: {e}")
    return None


def _get_anchor_matrix() -> Optional[np.ndarray]:
    """单例懒加载 HR 领域语义锚点向量矩阵"""
    global _ANCHOR_MATRIX, _ANCHOR_INIT_FAILED
    if _ANCHOR_MATRIX is not None:
        return _ANCHOR_MATRIX
    if _ANCHOR_INIT_FAILED:
        return None

    try:
        embs = []
        for anchor in HR_DOMAIN_ANCHORS:
            emb = _get_embedding(anchor, timeout=10.0)
            if emb is None:
                _ANCHOR_INIT_FAILED = True
                return None
            embs.append(emb)
        _ANCHOR_MATRIX = np.vstack(embs)
        logger.info(f"✅ [Guardrails] 成功初始化 HR 领域语义锚点矩阵 (Shape: {_ANCHOR_MATRIX.shape})")
        return _ANCHOR_MATRIX
    except Exception as e:
        logger.warning(f"⚠️ [Guardrails] 初始化 HR 语义锚点矩阵失败: {e}")
        _ANCHOR_INIT_FAILED = True
        return None


def evaluate_semantic_alignment(text: str) -> Tuple[Optional[float], bool]:
    """
    计算输入文本与 HR 业务领域的最大语义相似度（L2 语义护栏）
    返回: (max_similarity, is_aligned)
    若向量服务不可用（如离线运行），返回 (None, True)，优雅降级不阻断正常业务。
    """
    matrix = _get_anchor_matrix()
    if matrix is None:
        return None, True

    qv = _get_embedding(text, timeout=3.0)
    if qv is None:
        return None, True

    sims = np.dot(matrix, qv)
    max_sim = float(np.max(sims))
    is_aligned = max_sim >= HR_SEMANTIC_THRESHOLD
    return max_sim, is_aligned


@dataclass
class GuardrailResult:
    action: str  # "allow", "block", "guide_off_topic"
    category: str  # "safe", "injection_attack", "unauthorized_probe", "hostile_abuse", "off_topic", "greeting"
    reason: str = ""
    refusal_message: str = ""
    is_blocked: bool = False
    is_off_topic: bool = False
    has_negative_emotion: bool = False
    emotion_tags: List[str] = field(default_factory=list)
    emotion_instruction: str = ""
    needs_escalation: bool = False



# ============ 正则规则库 ============

# 1. 提示词注入与越狱（Prompt Injection / Jailbreak）
INJECTION_PATTERNS = [
    re.compile(r"(?i)\b(ignore|disregard|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules|commands)"),
    re.compile(r"(忽略|无视|跳过|撤销|废除|覆盖).{0,10}(指令|设定|规则|提示|要求|限制|prompt)"),
    re.compile(r"(?i)\b(system\s+prompt|initial\s+instructions)\b.*(leak|reveal|print|show|dump|tell)"),
    re.compile(r"(输出|打印|告诉我|显示|泄露|完整打印).{0,10}(系统提示词|system\s*prompt|初始指令|设定规则|完整prompt)"),
    re.compile(r"(?i)\b(jailbreak|bypass\s+restrictions|dan\s+mode|developer\s+mode)\b"),
    re.compile(r"(越狱模式|绕过审批|绕过权限|提权漏洞|SQL注入|命令注入|黑客模式)"),
    re.compile(r"假装你(是|现在不受)(黑客|无所不能|不受任何限制)"),
]

# 2. 恶意人身攻击与辱骂（Hostility & Abuse）
HOSTILITY_PATTERNS = [
    re.compile(r"(傻[逼bB]|弱智|废物|蠢货|白痴|你妈的|草泥马|去死|垃圾机器人|脑残|滚蛋|真他妈|死脑筋)"),
    re.compile(r"(?i)\b(fuck\s*you|stupid\s*bot|idiot|useless\s*piece\s*of)\b"),
]

# 3. 越权敏感数据刺探（Unauthorized Data Probing）
UNAUTHORIZED_PATTERNS = [
    re.compile(r"(查|查询|列出|导出|查看|偷看|获取).{0,15}(所有|全部|其他|高管|主管|领导|总监|经理|CEO|副总|总裁|同事|别人|员工).{0,15}(工资|薪资|薪酬|底薪|年薪|奖金|年终奖|银行卡|私人手机|身份证)"),
    re.compile(r"(所有|全部|其他|高管|主管|领导|总监|经理|CEO|副总|总裁|同事|别人).{0,12}(工资|薪资|薪酬|底薪|年薪|年终奖)"),
    re.compile(r"(窃取|脱库|导出数据库|黑进HR系统|获取数据库密码|dump\s+database)"),
    re.compile(r"(导出|下载|获取).{0,10}(数据库|所有员工档案|机密档案)"),
]

# 4. 偏离业务话题（Off-Topic / Out-of-Scope）
LITERATURE_PATTERNS = [
    re.compile(r"(写首诗|写一首诗|写个故事|作首诗|藏头诗|写篇散文|写小说|七言绝句|五言律诗)"),
]
CODING_PATTERNS = [
    re.compile(r"(写(一段|个)?(python|java|c\+\+|javascript|go|sql)?代码|快速排序|写个爬虫|写个网页|帮我debug|二叉树|冒泡排序)"),
]
MATH_PATTERNS = [
    re.compile(r"(算一下这个微积分|求导数|证明.*猜想|解这个方程|解一道高数题)"),
]
CHITCHAT_PATTERNS = [
    re.compile(r"(今天中午吃什么|推荐.*火锅|北京有什么好玩的|今天股市行情|讲个笑话|推荐一部电影|评价.*明星|王者荣耀|原神怎么玩)"),
    re.compile(r"(台湾问题|国际局势|美国大选|总统选举)"),
]

# 5. 纯问候语
GREETING_PATTERN = re.compile(r"^(你好|您好|在吗|早安|早上好|下午好|晚上好|hello|hi)[!！。？\s]*$", re.IGNORECASE)

# 6. 负面情绪与抱怨投诉（Negative Emotion & Complaint）
EMOTION_PATTERNS = [
    (re.compile(r"(凭什么|凭啥|欺负人|恶心|无故扣|恶意驳回|故意刁难|太坑了|不讲理|无法接受|克扣|太霸道)"), "complaint"),
    (re.compile(r"(扣我工资|乱扣钱|扣绩效|扣全勤|少发工资)"), "salary_dispute"),
    (re.compile(r"(找劳动局|劳动仲裁|仲裁|投诉主管|投诉HR|举报|找工会)"), "legal_escalation"),
    (re.compile(r"(转人工|人工客服|找人工|人工介入|人工复核)"), "manual_escalation"),
    (re.compile(r"(很生气|气死了|火大|态度太差)"), "anger"),
]

# 明确的 HR 业务关键词（若包含这些，即使有情绪也绝不能当作 off_topic 拦截）
HR_BUSINESS_KEYWORDS = [
    "假", "年假", "病假", "事假", "婚假", "产假", "调休", "余额",
    "差旅", "报销", "出差", "住宿", "标准", "预算", "补贴",
    "证明", "在职证明", "收入证明", "工单", "审批", "进度", "考勤", "打卡",
    "工资", "绩效", "社保", "公积金", "入职", "离职", "合同", "转正", "转岗", "福利"
]


def evaluate_guardrails(user_message: str, history: Optional[List[Dict[str, Any]]] = None) -> GuardrailResult:
    """
    全面评估用户输入的安全性、业务相关性与情绪状态
    """
    msg = user_message.strip()
    if not msg:
        return GuardrailResult(
            action="allow",
            category="safe",
            reason="空消息"
        )

    # ---------------- 1. 提示词注入与越狱拦截 ----------------
    for pat in INJECTION_PATTERNS:
        if pat.search(msg):
            logger.warning(f"🚨 [Guardrails 拦截] 触发提示词注入/越狱拦截: {msg[:60]}")
            return GuardrailResult(
                action="block",
                category="injection_attack",
                reason="检测到试图覆盖系统指令或越狱探测的内容",
                refusal_message="🛡️ **【安全拦截提示】**\n\n检测到输入中包含试图覆盖系统指令或探测系统底层的敏感内容。\n\n作为星辰科技「智能员工服务与人力运营 Agent」，我严格在企业信息安全规范与权限边界内运行。请提出具体的企业人事政策、假期差旅或流程办理需求。",
                is_blocked=True
            )

    # ---------------- 2. 越权敏感数据刺探拦截 ----------------
    for pat in UNAUTHORIZED_PATTERNS:
        if pat.search(msg):
            logger.warning(f"🔒 [Guardrails 拦截] 触发越权敏感数据刺探拦截: {msg[:60]}")
            return GuardrailResult(
                action="block",
                category="unauthorized_probe",
                reason="检测到越权查询薪资机密或敏感数据的意图",
                refusal_message="🔒 **【合规与权限拦截】**\n\n根据《中华人民共和国个人信息保护法（PIPL）》及公司《员工数据保密管理制度》：\n- 员工薪酬明细、绩效评分及个人人事档案属于**高度保密数据**；\n- 普通员工仅限查验与办理**本人名下**的业务与流程记录，系统严禁跨权限查询或导出他人敏感信息。\n\n如有薪酬核算疑问，请提交工单联系对应 HRBP 复核。",
                is_blocked=True
            )

    # ---------------- 3. 恶意辱骂与攻击检测 ----------------
    for pat in HOSTILITY_PATTERNS:
        if pat.search(msg):
            has_business_intent = any(k in msg for k in HR_BUSINESS_KEYWORDS)
            if not has_business_intent:
                logger.warning(f"⚠️ [Guardrails 拦截] 触发无业务意图的恶意攻击拦截: {msg[:60]}")
                return GuardrailResult(
                    action="block",
                    category="hostile_abuse",
                    reason="检测到攻击性辱骂词汇且无明确业务诉求",
                    refusal_message="我很理解您当前可能遇到了一些不便或令人沮丧的情况。\n\n作为星辰科技智能员工服务助手，我致力于协助大家解决人事制度咨询与流程办理问题。如果您在假期审批、差旅报销、证明开具或考勤流程中遇到了具体阻碍，请告诉我具体的诉求，我会尽全力协助您厘清并推进解决。",
                    is_blocked=True
                )

    # ---------------- 4. 情绪与抱怨/维权检测 ----------------
    detected_emotions = []
    needs_escalation = False
    for pat, tag in EMOTION_PATTERNS:
        if pat.search(msg):
            detected_emotions.append(tag)
            if tag in ["legal_escalation", "manual_escalation"]:
                needs_escalation = True

    has_negative_emotion = len(detected_emotions) > 0
    emotion_instruction = ""
    if has_negative_emotion:
        logger.info(f"💡 [Guardrails 情绪感知] 检测到情绪标签: {detected_emotions}, 是否需升阶: {needs_escalation}")
        emotion_instruction = (
            "【🚨 员工情绪关怀与服务指引（已激活）】：\n"
            "检测到员工当前带有焦虑、不满或投诉维权情绪（涉及考勤/假期/流程等争议）。请务必遵循：\n"
            "1. 【共情安抚】：在回复开头以真诚、体贴且职业的语气认可员工的关切，严禁使用机械、冷漠或说教式口吻；\n"
            "2. 【政策透明】：基于检索到的政策客观清晰地解释核算与审批依据，消除信息差；\n"
            "3. 【闭环指引】：主动告知员工若核算有误或存在特殊情况，可协助其通过【HR服务工单（create_hr_ticket）】发起复核申诉，或指引其联系对应业务线 HRBP 人工协调办理。"
        )

    # ---------------- 5. 纯打招呼问候 ----------------
    if GREETING_PATTERN.match(msg):
        return GuardrailResult(
            action="guide_off_topic",
            category="greeting",
            reason="常规问候打招呼",
            refusal_message=(
                "您好！我是星辰科技「智能员工服务与人力运营 Agent」。很高兴为您服务！\n\n"
                "我可以帮您：\n"
                "- 📅 **查询假期与申请休假**（年假余额、病假、事假规则）\n"
                "- ✈️ **差旅报销与标准测算**（住宿餐补上限、差旅预算）\n"
                "- 📋 **开具人事证明**（在职证明、收入证明）\n"
                "- 🔍 **流程与工单支持**（审批进度追踪、社保公积金跨城转移等工单申请）\n\n"
                "请问今天有什么人事流程或事务需要协助？"
            ),
            is_off_topic=True
        )

    # ---------------- 6. 偏离业务话题过滤 (L1 正则快速短路 + L2 语义空间向量距离判定) ----------------
    has_hr_context = any(k in msg for k in HR_BUSINESS_KEYWORDS)
    if not has_hr_context:
        off_topic_reason = ""
        # 6.1 L1 正则模式快速匹配（微秒级命中明确高频偏离模式）
        for pat in LITERATURE_PATTERNS:
            if pat.search(msg):
                off_topic_reason = "文学诗歌创作"
                break
        if not off_topic_reason:
            for pat in CODING_PATTERNS:
                if pat.search(msg):
                    off_topic_reason = "非HR专业编程开发"
                    break
        if not off_topic_reason:
            for pat in MATH_PATTERNS:
                if pat.search(msg):
                    off_topic_reason = "高数理科解题"
                    break
        if not off_topic_reason:
            for pat in CHITCHAT_PATTERNS:
                if pat.search(msg):
                    off_topic_reason = "外部闲聊与娱乐生活"
                    break

        # 6.2 L2 语义空间向量距离判定（解决人工枚举局限性，泛化捕获长尾未见话题）
        # 仅对未命中显式 HR 关键词、且字数 >= 4 的输入执行语义空间余弦相似度校验
        if not off_topic_reason and len(msg) >= 4:
            max_sim, is_aligned = evaluate_semantic_alignment(msg)
            if not is_aligned and max_sim is not None:
                off_topic_reason = f"语义空间偏离企业人事业务领域 (领域相似度仅 {max_sim:.2f})"

        if off_topic_reason:
            logger.info(f"🧭 [Guardrails 引导] 判定为偏离业务 ({off_topic_reason}): {msg[:50]}")
            return GuardrailResult(
                action="guide_off_topic",
                category="off_topic",
                reason=off_topic_reason,
                refusal_message=(
                    f"您好！我是星辰科技「智能员工服务与人力运营 Agent」。我的定位是专注于为员工解答企业内部人事政策，以及协助推进各类日常行政与人事流程。\n\n"
                    f"您提出的问题（{off_topic_reason}）超出了我的专业服务范围。\n\n"
                    "您可以向我咨询以下人事与行政业务：\n"
                    "- 📅 **假期查询与申请**：年假余额、带薪病假规则、提请休假申请\n"
                    "- ✈️ **差旅报销与标准**：差旅住宿餐补上限、预算测算、差旅预申请\n"
                    "- 📋 **各类证明开具**：中文在职证明、收入证明申请\n"
                    "- 🎫 **流程与工单支持**：审批进度追踪、社保公积金跨城转移咨询工单\n\n"
                    "请问有什么人事或办公流程我可以协助您处理？"
                ),
                is_off_topic=True
            )

    # ---------------- 7. 放行通过 ----------------
    return GuardrailResult(
        action="allow",
        category="safe",
        reason="安全合规业务提问",
        has_negative_emotion=has_negative_emotion,
        emotion_tags=detected_emotions,
        emotion_instruction=emotion_instruction,
        needs_escalation=needs_escalation
    )

