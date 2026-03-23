export type AssistedStatus = 'standby' | 'challenge_required' | 'waiting_human' | 'resumed' | 'failed';

export const assistedGuidance: Record<
  AssistedStatus,
  {
    label: string;
    description: string;
    actionLabel?: string;
    actionHint?: string;
    actionUrl?: string;
  }
> = {
  standby: {
    label: '准备就绪',
    description: '工作台已经待命。填写关键词、城市和简历内容后，系统会开始返回职位来源与执行进度。',
  },
  challenge_required: {
    label: '需要人工验证',
    description: '当前流程遇到验证码、身份确认或安全校验。这里不会假装自动完成，而是明确要求你接管。',
    actionLabel: '前往验证中心',
    actionHint: '验证完成后，系统会继续执行，不需要从头再来。',
  },
  waiting_human: {
    label: '等待人工处理',
    description: '当前链路存在阻塞或疑点，需要人工确认后继续。先处理阻塞，再看系统恢复执行。',
    actionLabel: '我已完成处理',
    actionHint: '处理完成后重新触发，本次记录会继续保留。',
  },
  resumed: {
    label: '已恢复执行',
    description: '人工步骤已经完成，系统恢复推进。本次日志会继续更新，不会中断上下文。',
  },
  failed: {
    label: '执行失败',
    description: '流程遇到异常。先检查提示，再重新触发，避免带着错误上下文继续跑。',
    actionLabel: '重新触发',
    actionHint: '重新开始前，先确认关键词、城市、登录状态和简历内容。',
  },
};

const normalizedStatus = (value: string | undefined): AssistedStatus => {
  if (!value) {
    return 'standby';
  }
  const normalized = value.toLowerCase();
  if (normalized.includes('challenge_required')) {
    return 'challenge_required';
  }
  if (normalized.includes('waiting_human')) {
    return 'waiting_human';
  }
  if (normalized.includes('resumed')) {
    return 'resumed';
  }
  if (normalized.includes('failed')) {
    return 'failed';
  }
  return 'standby';
};

export const deriveAssistedStatus = (payload: {
  assisted_status?: string;
  stage?: string;
}): AssistedStatus => {
  const assisted = normalizedStatus(payload.assisted_status);
  if (assisted !== 'standby') {
    return assisted;
  }
  return normalizedStatus(payload.stage);
};