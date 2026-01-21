# rss_config.py
# RSS 源配置文件
# 用于存储所有 RSS 源的 URL 和名称，便于集中管理和维护

RSS_SOURCES = [
    # ===== A. 一线科技 / 投资媒体 =====
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "Bloomberg Technology", "url": "https://www.bloomberg.com/feeds/podcasts/technology.xml"},
    {"name": "Reuters Technology", "url": "https://www.reuters.com/rssFeed/technologyNews"},
    {"name": "CNBC Technology", "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Financial Times Technology", "url": "https://www.ft.com/technology?format=rss"},
    {"name": "Wall Street Journal Tech", "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml"},

    # ===== B. AI 专业媒体 =====
    {"name": "The Decoder", "url": "https://the-decoder.com/feed/"},
    {"name": "Synced Review", "url": "https://syncedreview.com/feed/"},
    {"name": "AI Trends", "url": "https://www.aitrends.com/feed/"},
    {"name": "MarkTechPost", "url": "https://www.marktechpost.com/feed/"},
    {"name": "Analytics India Magazine", "url": "https://analyticsindiamag.com/feed/"},
    {"name": "Towards Data Science", "url": "https://towardsdatascience.com/feed"},
    {"name": "KDnuggets", "url": "https://www.kdnuggets.com/feed"},
    {"name": "Machine Learning Mastery", "url": "https://machinelearningmastery.com/feed/"},
    {"name": "Import AI", "url": "https://jack-clark.net/feed/"},
    {"name": "AI Alignment Forum", "url": "https://www.alignmentforum.org/feed.xml"},

    # ===== C. 大厂官方 =====
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss/"},
    {"name": "Google AI Blog", "url": "https://ai.googleblog.com/feeds/posts/default"},
    {"name": "Meta AI", "url": "https://ai.facebook.com/blog/rss/"},
    {"name": "Microsoft AI", "url": "https://blogs.microsoft.com/ai/feed/"},
    {"name": "Amazon Science", "url": "https://www.amazon.science/rss"},
    {"name": "NVIDIA Blog", "url": "https://blogs.nvidia.com/feed/"},
    {"name": "Apple Machine Learning", "url": "https://machinelearning.apple.com/rss.xml"},
    {"name": "DeepMind Blog", "url": "https://www.deepmind.com/blog/rss.xml"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/rss.xml"},

    # ===== D. 投融资 / 创投 =====
    {"name": "Crunchbase News", "url": "https://news.crunchbase.com/feed/"},
    {"name": "PitchBook News", "url": "https://pitchbook.com/news/rss"},
    {"name": "CB Insights", "url": "https://www.cbinsights.com/research/feed/"},
    {"name": "Sifted", "url": "https://sifted.eu/feed/"},
    {"name": "Tech.eu", "url": "https://tech.eu/feed/"},
    {"name": "VC News Daily", "url": "https://vcnewsdaily.com/feed/"},
    {"name": "StrictlyVC", "url": "https://www.strictlyvc.com/feed/"},
    {"name": "Axios Technology", "url": "https://www.axios.com/technology/rss.xml"},
    {"name": "Semafor Technology", "url": "https://www.semafor.com/rss/technology.xml"},
    {"name": "Protocol", "url": "https://www.protocol.com/feed"},

    # ===== E. 芯片 / 半导体 / AI Infra =====
    {"name": "SemiAnalysis", "url": "https://semianalysis.com/feed/"},
    {"name": "AnandTech", "url": "https://www.anandtech.com/rss/"},
    {"name": "Tom's Hardware", "url": "https://www.tomshardware.com/feeds/all"},
    {"name": "EE Times", "url": "https://www.eetimes.com/feed/"},
    {"name": "The Register", "url": "https://www.theregister.com/headlines.atom"},
    {"name": "Semiconductor Engineering", "url": "https://semiengineering.com/feed/"},
    {"name": "Blocks and Files", "url": "https://blocksandfiles.com/feed/"},
    {"name": "ServeTheHome", "url": "https://www.servethehome.com/feed/"},
    {"name": "Data Center Dynamics", "url": "https://www.datacenterdynamics.com/en/rss/"},
    {"name": "HPCwire", "url": "https://www.hpcwire.com/feed/"},

    # ===== F. 社区 / 真实信号 =====
    {"name": "Hacker News AI", "url": "https://hnrss.org/newest?q=AI"},
    {"name": "Hacker News Frontpage", "url": "https://hnrss.org/frontpage"},
    {"name": "Reddit MachineLearning", "url": "https://www.reddit.com/r/MachineLearning/.rss"},
    {"name": "Reddit Artificial", "url": "https://www.reddit.com/r/artificial/.rss"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed"},
    {"name": "Y Combinator Blog", "url": "https://www.ycombinator.com/blog/feed"},
    {"name": "Andreessen Horowitz", "url": "https://a16z.com/feed/"},
    {"name": "GitHub Trending", "url": "https://github.com/trending?since=daily"},

    # ===== G. 研究 / 长期趋势 =====
    {"name": "arXiv AI", "url": "https://export.arxiv.org/rss/cs.AI"},
    {"name": "arXiv Machine Learning", "url": "https://export.arxiv.org/rss/cs.LG"},
    {"name": "Stanford HAI", "url": "https://hai.stanford.edu/rss.xml"},
    {"name": "MIT CSAIL", "url": "https://www.csail.mit.edu/rss.xml"},
    {"name": "Berkeley AI Research", "url": "https://bair.berkeley.edu/blog/feed.xml"},
    {"name": "Allen AI Blog", "url": "https://allenai.org/blog/rss.xml"},
    {"name": "DeepLearning.AI", "url": "https://www.deeplearning.ai/blog/feed/"},
    {"name": "Distill", "url": "https://distill.pub/rss.xml"},
    {"name": "AI Now Institute", "url": "https://ainowinstitute.org/feed.xml"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/rss/fulltext"}
]


# 搜索参数配置
SEARCH_HOURS = 24  # 默认搜索时间范围（小时）
MAX_ITEMS_PER_SOURCE = 20  # 每个 RSS 源最大条数
MAX_NORMALIZED_ITEMS = 500  # 规范化输出的最大条数
