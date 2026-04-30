export type Language = 'en' | 'zh';

export const translations = {
  en: {
    // Sidebar
    workspace: 'WORKSPACE',
    signals: 'Signals',
    opportunities: 'Opportunities',
    reports: 'Reports',
    sources: 'Sources',
    runs: 'Runs',
    settings: 'Settings',
    
    // Header
    searchPlaceholder: 'Search opportunities, sources...',
    engineReady: 'Engine Ready',
    lastRun: 'Last run: 10m ago',
    generateReport: 'Generate Report',
    runScan: 'Run Scan',
    
    // Workspace
    allOpportunities: 'All Opportunities',
    filter: 'Filter',
    sort: 'Sort',
    colRating: 'Rating',
    colTitle: 'Title',
    colScore: 'Score',
    colSource: 'Source',
    colDate: 'Date',
    placeholderTitle: 'Module',
    placeholderDesc: 'This module is currently a placeholder for future features.',
    
    // Inspector
    detail: 'Detail',
    optDetail: 'Opportunity Detail',
    openOriginal: 'Open Original',
    aiSummary: 'AI Summary & Insight',
    keyInsight: 'Key Insight',
    actionItems: 'Action Items',
    fiveDimScore: '5-Dimension Score',
    redlineTriggered: 'Redline Triggered',
    detailPlaceholder: 'Details will be shown here.',

    // Landing Page
    login: 'Log in',
    register: 'Sign up',
    dashboard: 'Dashboard',
    heroBadge: 'SaaS Idea Validation Engine V4.1',
    heroTitle1: 'Build what people',
    heroTitle2: 'actually want.',
    heroDesc: 'Stop guessing. GoldIdeas captures live signals from developer communities and analyzes them with an advanced 5-dimension rule engine to find your next Micro-SaaS goldmine.',
    getStarted: 'Start Validating Now',
    viewDemo: 'View Documentation',
    trustedBy: 'TRUSTED BY INDIE HACKERS FROM',
    feat1Title: 'Live Community Signals',
    feat1Desc: 'We monitor HackerNews, Reddit, and IndieHackers 24/7 to capture authentic pain points, complaints, and willingness to pay.',
    feat2Title: '5-Dimension Scoring Engine',
    feat2Desc: 'Every idea is rigorously evaluated across Pain Level, Dev Fit, Stability, Growth Potential, and Monetization Viability.',
    feat3Title: 'Zero-BS Reporting',
    feat3Desc: 'No generic AI fluff. Our pure Python rule engine provides highly structured, actionable reports with clear redlines.',
    stepTitle: 'How GoldIdeas Works',
    step1Title: '1. Ingest',
    step1Desc: 'Raw signals are pulled from multiple developer forums.',
    step2Title: '2. Analyze',
    step2Desc: 'The rules engine filters noise and scores viable ideas.',
    step3Title: '3. Execute',
    step3Desc: 'You receive a curated dashboard of validated Micro-SaaS opportunities.',
    bottomCtaTitle: 'Ready to build your next product?',
    bottomCtaDesc: 'Join the platform that turns developer complaints into profitable businesses.',
    footerCopyright: '© 2026 GoldIdeas. All rights reserved.',
  },
  zh: {
    // Sidebar
    workspace: '工作区',
    signals: '原始信号',
    opportunities: '商业机会',
    reports: '分析报告',
    sources: '信息源',
    runs: '扫描历史',
    settings: '系统设置',
    
    // Header
    searchPlaceholder: '搜索机会、信息源...',
    engineReady: '引擎就绪',
    lastRun: '上次运行: 10分钟前',
    generateReport: '生成报告',
    runScan: '运行扫描',
    
    // Workspace
    allOpportunities: '所有机会',
    filter: '筛选',
    sort: '排序',
    colRating: '评级',
    colTitle: '标题',
    colScore: '评分',
    colSource: '来源',
    colDate: '日期',
    placeholderTitle: '模块',
    placeholderDesc: '该模块当前为预留位，功能正在开发中。',
    
    // Inspector
    detail: '详情',
    optDetail: '机会详情',
    openOriginal: '查看原文',
    aiSummary: 'AI 摘要与洞察',
    keyInsight: '核心洞察',
    actionItems: '落地建议',
    fiveDimScore: '五维评分',
    redlineTriggered: '触发红线',
    detailPlaceholder: '详情内容将在此显示。',

    // Landing Page
    login: '登录',
    register: '注册',
    dashboard: '进入工作台',
    heroBadge: 'SaaS 商业分析引擎 V4.1',
    heroTitle1: '构建真正被',
    heroTitle2: '需要的产品。',
    heroDesc: '告别盲目开发。GoldIdeas 全天候监听开发者社区的真实痛点，通过高阶五维规则引擎，为您挖掘下一个高转化率的 Micro-SaaS 商业金矿。',
    getStarted: '立即开始验证',
    viewDemo: '查看技术文档',
    trustedBy: '受到以下社区独立开发者的信赖',
    feat1Title: '全网高频痛点监控',
    feat1Desc: '深度接入 HackerNews, Reddit, V2EX 等社区，精准捕捉开发者的抱怨、求助与付费意愿，拒绝伪需求。',
    feat2Title: '五维度硬核评分',
    feat2Desc: '自动对所有收集到的信号进行「痛点强度、开发性价比、生存稳定性、获客阻力、变现确定性」五大维度的量化评估。',
    feat3Title: '拒绝 AI 废话',
    feat3Desc: '完全基于结构化的 Python 本地规则引擎，不依赖昂贵的 LLM API，提供直指核心的商业落地建议与红线警告。',
    stepTitle: '工作流拆解',
    step1Title: '1. 信号采集',
    step1Desc: '爬虫矩阵实时抓取各大极客论坛的未解决需求。',
    step2Title: '2. 引擎清洗',
    step2Desc: '过滤噪音数据，利用多维规则引擎计算商业可行性。',
    step3Title: '3. 落地输出',
    step3Desc: '在工作台呈现经过严格筛选的黄金点子，附带完整执行策略。',
    bottomCtaTitle: '准备好打造下一个爆款产品了吗？',
    bottomCtaDesc: '加入我们，将全网开发者的痛点转化为您的持续性收入。',
    footerCopyright: '© 2026 GoldIdeas. 保留所有权利。',
  }
};

export const useTranslation = (lang: Language) => {
  return (key: string) => {
    const translationKey = key as keyof typeof translations['en'];
    return translations[lang][translationKey] || translations['en'][translationKey] || key;
  };
};
