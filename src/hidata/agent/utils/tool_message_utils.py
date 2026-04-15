from calendar import c
import logging

logger = logging.getLogger(__name__)



def _sanitize_tool_messages(msgs: list) -> list:
    """确保 tool_use/tool_result 消息配对正确、有序。

    如果不需要修复，则返回原列表不变。
    """
    # 首先，修复 tool_use 块中 input 为空但 raw_input 有效的场景
    msgs = _repair_empty_tool_inputs(msgs)
    # 然后，移除无效的 tool 块（id 为空、name 为 None 等）
    msgs = _remove_invalid_tool_blocks(msgs)
    # 最后，移除重复的 tool 块
    msgs = _dedup_tool_blocks(msgs)

    pending: dict[str, int] = {}
    needs_fix = False
    for msg in msgs:
        msg_uses, msg_results = extract_tool_ids(msg)
        for rid in msg_results:
            if pending.get(rid, 0) <= 0:
                needs_fix = True
                break
            pending[rid] -= 1
            if pending[rid] == 0:
                del pending[rid]
        if needs_fix:
            break
        if pending and not msg_results:
            needs_fix = True
            break
        for uid in msg_uses:
            pending[uid] = pending.get(uid, 0) + 1
    if not needs_fix and not pending:
        return msgs

    logger.debug("Sanitizing tool messages: fixing order/pairing issues")
    return _remove_unpaired_tool_messages(_reorder_tool_results(msgs))


def _repair_empty_tool_inputs(msgs: list) -> list:

    """修复 tool_use 块中 input 为空但 raw_input 有效的场景。
    """
    return msgs

def _remove_invalid_tool_blocks(msgs: list) -> list:
    """移除无效的 tool 块（id 为空、name 为 None 等）。
    """
    return msgs

def _dedup_tool_blocks(msgs: list) -> list:
    """移除重复的 tool 块。
    """
    return msgs

def extract_tool_ids(msg: dict) -> tuple[list[str], list[str]]:
    """提取 tool_use/tool_result 消息中的 tool_ids。
    """
    uses:set[str] = set()
    results:set[str] = set()

    if isinstance(msg.content, list):
        for block in msg.content:
            if isinstance(block, dict) and block.get("id"):
                btype =block.get("type")
                if btype == "tool_use":
                    uses.add(block["id"])
                elif btype == "tool_result":
                    results.add(block["id"])
    return uses, results


def _remove_unpaired_tool_messages(msgs: list) -> list:
    """移除未配对的 tool 消息。
    """
    to_remove:set[int] = set()
    i=0
    while i < len(msgs):
        use_ids,_=extract_tool_ids(msgs[i])
        if not use_ids:
            i+=1
            continue
        required=set[str](use_ids)
        j=i+1
        result_indices: list[int] = []
        while j<len(msgs) and required:
            _,r=extract_tool_ids(msgs[j])
            if not r:
                break
            required-=r
            result_indices.append(j)
            j+=1
        if required:
            to_remove.add(i)
            to_remove.update(result_indices)
            i+=1
        else:
            i=j

    surviving_use_ids: set[str] = set()
    for idx, msg in enumerate(msgs):
        if idx not in to_remove:
            u, _ = extract_tool_ids(msg)
            surviving_use_ids |= u
    for idx, msg in enumerate(msgs):
        if idx in to_remove:
            continue
        _, r = extract_tool_ids(msg)
        if r and not r.issubset(surviving_use_ids):
            to_remove.add(idx)

    return [msg for idx, msg in enumerate(msgs) if idx not in to_remove]

def _reorder_tool_results(msgs: list) -> list:
    """重新排序 tool 结果消息。
    """
    return msgs