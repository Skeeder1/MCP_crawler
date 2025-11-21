INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'f3e7b8cf-5917-40d5-9ee8-3808c91880c8',
    'perplexity',
    'Perplexity Ask MCP Server',
    'Perplexity Ask MCP Server',
    'Perplexity Ask MCP Server is a Model Context Protocol Server connector for the Perplexity API, enabling web search capabilities within the MCP ecosystem.',
    'Perplexity Ask MCP Server is a Model Context Protocol Server connector for the Perplexity API, enabling web search capabilities within the MCP ecosystem.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'ppl-ai',
    'ppl-ai',
    '2025-11-19 20:24:19.387268',
    '2025-11-19 20:24:19.387268',
    '2025-11-19 20:24:19.387268'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '8ecf2939-9cff-41a5-8b71-0b1b67410c84',
    'gitlab',
    'GitLab',
    'GitLab',
    'GitLab MCP Server is an API that enables project management and file operations through the GitLab platform. It facilitates various Git-related tasks using a user-friendly interface.',
    'GitLab MCP Server is an API that enables project management and file operations through the GitLab platform. It facilitates various Git-related tasks using a user-friendly interface.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:24:25.600649',
    '2025-11-19 20:24:25.600649',
    '2025-11-19 20:24:25.600649'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'eaaebe04-276c-4a65-83bb-2a64b87f3208',
    'zhipu-web-search',
    'Zhipu Web Search',
    'Zhipu Web Search',
    'Zhipu Web Search is a specialized search engine designed for large models, integrating four different search engines to allow users to compare and switch between them flexibly. It enhances traditional',
    'Zhipu Web Search is a specialized search engine designed for large models, integrating four different search engines to allow users to compare and switch between them flexibly. It enhances traditional web crawling and ranking capabilities with improved intent recognition, providing results tailored for large model processing.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'BigModel',
    'BigModel',
    '2025-11-19 20:24:30.092901',
    '2025-11-19 20:24:30.092901',
    '2025-11-19 20:24:30.092901'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '6de7ceda-ec06-4079-8ad6-4c4f32136c51',
    'jina-mcp-tools',
    'Jina AI MCP Tools',
    'Jina AI MCP Tools',
    'Jina AI MCP Tools is a Model Context Protocol (MCP) server that integrates with Jina AI Search Foundation APIs, enabling users to access various AI-driven tools for web reading, searching, and fact-ch',
    'Jina AI MCP Tools is a Model Context Protocol (MCP) server that integrates with Jina AI Search Foundation APIs, enabling users to access various AI-driven tools for web reading, searching, and fact-checking.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'PsychArch',
    'PsychArch',
    '2025-11-19 20:24:35.346401',
    '2025-11-19 20:24:35.346401',
    '2025-11-19 20:24:35.346401'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'c61e58ee-118b-42d6-96fd-c7b2b6f49b3e',
    'everart',
    'EverArt',
    'EverArt',
    'EverArt is an AI image generation tool that allows users to create images using various models through an API.',
    'EverArt is an AI image generation tool that allows users to create images using various models through an API.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:24:41.356657',
    '2025-11-19 20:24:41.356657',
    '2025-11-19 20:24:41.356657'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'b776f564-1d5f-4f72-92e7-53e65f20d558',
    'postgres',
    'PostgreSQL',
    'PostgreSQL',
    'PostgreSQL is a Model Context Protocol server providing read-only access to PostgreSQL databases, allowing for schema inspection and execution of read-only queries.',
    'PostgreSQL is a Model Context Protocol server providing read-only access to PostgreSQL databases, allowing for schema inspection and execution of read-only queries.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:24:46.937167',
    '2025-11-19 20:24:46.937167',
    '2025-11-19 20:24:46.937167'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '23c1b37b-5de2-4abe-aa2d-e970fffaeea1',
    'context7',
    'Context7',
    'Context7',
    'Context7 is a server that provides up-to-date documentation for large language models (LLMs) and AI code editors, ensuring that users have access to the latest information and code examples.',
    'Context7 is a server that provides up-to-date documentation for large language models (LLMs) and AI code editors, ensuring that users have access to the latest information and code examples.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'upstash',
    'upstash',
    '2025-11-19 20:24:52.223348',
    '2025-11-19 20:24:52.223348',
    '2025-11-19 20:24:52.223348'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '90e14098-d2d6-4ff0-9ca4-6638fa88c1a8',
    'time',
    'Time',
    'Time',
    'Time MCP Server is a Model Context Protocol server that provides time and timezone conversion capabilities. It enables LLMs to get current time information and perform timezone conversions using IANA ',
    'Time MCP Server is a Model Context Protocol server that provides time and timezone conversion capabilities. It enables LLMs to get current time information and perform timezone conversions using IANA timezone names, with automatic system timezone detection.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:24:57.721260',
    '2025-11-19 20:24:57.721260',
    '2025-11-19 20:24:57.721260'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'a1671267-714f-4ccf-86a2-a409bfd7d5d1',
    'firecrawl-mcp-server',
    'Firecrawl Mcp Server',
    'Firecrawl Mcp Server',
    'Firecrawl MCP Server is an implementation of the Model Context Protocol (MCP) that enhances web scraping capabilities for various LLM clients, including Cursor and Claude.',
    'Firecrawl MCP Server is an implementation of the Model Context Protocol (MCP) that enhances web scraping capabilities for various LLM clients, including Cursor and Claude.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'mendableai',
    'mendableai',
    '2025-11-19 20:25:03.753106',
    '2025-11-19 20:25:03.753106',
    '2025-11-19 20:25:03.753106'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '7928e1f5-0a30-4ec0-bc43-ac513280f4ba',
    'puppeteer',
    'Puppeteer',
    'Puppeteer',
    'Puppeteer is a Model Context Protocol server that provides browser automation capabilities, allowing LLMs to interact with web pages, take screenshots, and execute JavaScript in a real browser environ',
    'Puppeteer is a Model Context Protocol server that provides browser automation capabilities, allowing LLMs to interact with web pages, take screenshots, and execute JavaScript in a real browser environment.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:25:09.417038',
    '2025-11-19 20:25:09.417038',
    '2025-11-19 20:25:09.417038'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '6aa8cb8c-5368-4eca-86a7-df30c0f73dcf',
    'minimax-mcp',
    'MiniMax MCP',
    'MiniMax MCP',
    'MiniMax MCP is an official server for the MiniMax Model Context Protocol that facilitates interaction with advanced Text to Speech and video/image generation APIs.',
    'MiniMax MCP is an official server for the MiniMax Model Context Protocol that facilitates interaction with advanced Text to Speech and video/image generation APIs.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'MiniMax-AI',
    'MiniMax-AI',
    '2025-11-19 20:25:15.078834',
    '2025-11-19 20:25:15.078834',
    '2025-11-19 20:25:15.078834'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '4221a213-b1ce-4207-88eb-1c7ef03f9aa1',
    'edgeone-pages-mcp',
    'EdgeOne Pages MCP',
    'EdgeOne Pages MCP',
    'EdgeOne Pages MCP is a service designed for deploying HTML content to EdgeOne Pages, allowing users to obtain a publicly accessible URL for their content.',
    'EdgeOne Pages MCP is a service designed for deploying HTML content to EdgeOne Pages, allowing users to obtain a publicly accessible URL for their content.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'TencentEdgeOne',
    'TencentEdgeOne',
    '2025-11-19 20:25:20.162980',
    '2025-11-19 20:25:20.162980',
    '2025-11-19 20:25:20.162980'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'ad7eabc4-d487-4de9-99df-70d0613d642e',
    'mcp-server-flomo',
    'mcp-server-flomo MCP Server',
    'mcp-server-flomo MCP Server',
    'MCP Server Flomo is a TypeScript-based server that allows users to write notes directly to Flomo, a note-taking application.',
    'MCP Server Flomo is a TypeScript-based server that allows users to write notes directly to Flomo, a note-taking application.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'chatmcp',
    'chatmcp',
    '2025-11-19 20:25:25.426658',
    '2025-11-19 20:25:25.426658',
    '2025-11-19 20:25:25.426658'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '890bd7d9-c73c-47c4-87b5-aee511110fad',
    'playwright-mcp',
    'Playwright Mcp',
    'Playwright Mcp',
    'Playwright MCP is a Model Context Protocol server that provides browser automation capabilities using Playwright. It allows large language models (LLMs) to interact with web pages through structured a',
    'Playwright MCP is a Model Context Protocol server that provides browser automation capabilities using Playwright. It allows large language models (LLMs) to interact with web pages through structured accessibility snapshots, eliminating the need for screenshots or visually-tuned models.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'microsoft',
    'microsoft',
    '2025-11-19 20:25:30.499202',
    '2025-11-19 20:25:30.499202',
    '2025-11-19 20:25:30.499202'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    'ec7ad662-3fbb-4a5e-b71b-180724a244c6',
    'amap-maps',
    'Amap Maps',
    'Amap Maps',
    'Amap Maps is a server that supports any MCP protocol client, allowing users to easily utilize the Amap Maps MCP server for various location-based services.',
    'Amap Maps is a server that supports any MCP protocol client, allowing users to easily utilize the Amap Maps MCP server for various location-based services.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'amap',
    'amap',
    '2025-11-19 20:25:36.875669',
    '2025-11-19 20:25:36.875669',
    '2025-11-19 20:25:36.875669'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '3e2ad477-2e25-4b7f-a909-8a941cb42711',
    'server',
    'Search1API',
    'Search1API',
    'Search1API is an API that provides integrated functionalities for web search, crawling, and sitemap extraction.',
    'Search1API is an API that provides integrated functionalities for web search, crawling, and sitemap extraction.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'search1api',
    'search1api',
    '2025-11-19 20:25:42.631289',
    '2025-11-19 20:25:42.631289',
    '2025-11-19 20:25:42.631289'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '37c81b61-b2ce-470c-8e56-a13e2578f440',
    'aws-kb-retrieval-server',
    'Aws Kb Retrieval Server',
    'Aws Kb Retrieval Server',
    'The AWS Knowledge Base Retrieval Server is an MCP server implementation designed to retrieve information from the AWS Knowledge Base using the Bedrock Agent Runtime.',
    'The AWS Knowledge Base Retrieval Server is an MCP server implementation designed to retrieve information from the AWS Knowledge Base using the Bedrock Agent Runtime.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:25:48.413986',
    '2025-11-19 20:25:48.413986',
    '2025-11-19 20:25:48.413986'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '8dbe6649-3cc3-4830-86e4-23cd4d526653',
    'sentry',
    'Sentry',
    'Sentry',
    'Sentry is a Model Context Protocol server designed for retrieving and analyzing issues from Sentry.io. It enables developers to inspect error reports, stack traces, and debugging information efficient',
    'Sentry is a Model Context Protocol server designed for retrieving and analyzing issues from Sentry.io. It enables developers to inspect error reports, stack traces, and debugging information efficiently.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:26:00.865523',
    '2025-11-19 20:26:00.865523',
    '2025-11-19 20:26:00.865523'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '45f77aa6-f3d0-41ac-8024-d5e79f83dd19',
    'howtocook-mcp',
    'Howtocook Mcp',
    'Howtocook Mcp',
    'ShipAny Two Released. Ship Your AI SaaS startups in hours',
    'ShipAny Two Released. Ship Your AI SaaS startups in hours',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'worryzyy',
    'worryzyy',
    '2025-11-19 20:26:06.161912',
    '2025-11-19 20:26:06.161912',
    '2025-11-19 20:26:06.161912'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '6a2a33d5-dd0c-41fb-8c87-5e56035f0876',
    'serper-mcp-server',
    'Serper MCP Server',
    'Serper MCP Server',
    'Serper MCP Server is a Model Context Protocol server that provides Google Search via Serper, enabling LLMs to retrieve search result information from Google.',
    'Serper MCP Server is a Model Context Protocol server that provides Google Search via Serper, enabling LLMs to retrieve search result information from Google.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'garymengcom',
    'garymengcom',
    '2025-11-19 20:26:12.397745',
    '2025-11-19 20:26:12.397745',
    '2025-11-19 20:26:12.397745'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '2ae58afd-465b-4be8-9b80-4e46793edc76',
    'redis',
    'Redis',
    'Redis',
    'Redis is a Model Context Protocol server that provides access to Redis databases, enabling LLMs to interact with Redis key-value stores through standardized tools.',
    'Redis is a Model Context Protocol server that provides access to Redis databases, enabling LLMs to interact with Redis key-value stores through standardized tools.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'modelcontextprotocol',
    'modelcontextprotocol',
    '2025-11-19 20:26:18.115958',
    '2025-11-19 20:26:18.115958',
    '2025-11-19 20:26:18.115958'
) ON CONFLICT (id) DO NOTHING;
INSERT INTO mcp_hub.servers
(id, slug, name, display_name, tagline, short_description, logo_url, homepage_url,
 install_count, favorite_count, tools_count, status, verification_status,
 creator_id, creator_name, creator_username, created_at, published_at, updated_at)
VALUES (
    '088846a5-c235-413f-8b04-145b3617f8aa',
    'mcpadvisor',
    'MCP Advisor',
    'MCP Advisor',
    'MCP Advisor is a discovery and recommendation service designed to help users explore Model Context Protocol (MCP) servers. It acts as a smart guide for AI assistants, enabling them to find and underst',
    'MCP Advisor is a discovery and recommendation service designed to help users explore Model Context Protocol (MCP) servers. It acts as a smart guide for AI assistants, enabling them to find and understand available MCP services through natural language queries.',
    NULL,
    NULL,
    0,
    0,
    0,
    'approved',
    'unverified',
    NULL,
    'istarwyh',
    'istarwyh',
    '2025-11-19 20:26:23.656792',
    '2025-11-19 20:26:23.656792',
    '2025-11-19 20:26:23.656792'
) ON CONFLICT (id) DO NOTHING;
