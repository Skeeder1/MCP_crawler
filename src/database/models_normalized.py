"""
SQLAlchemy Models for MCP Servers Database (Normalized SQLite Schema)
11 tables with proper separation of concerns
"""
import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, ForeignKey, DateTime,
    CheckConstraint, UniqueConstraint, event
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


# ============================================================================
# Core Models
# ============================================================================

class Server(Base):
    """
    Core server model - stores basic server metadata
    """
    __tablename__ = 'servers'

    # Identifiers
    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Basic information
    name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    tagline = Column(Text, nullable=False, default='')
    short_description = Column(Text, nullable=False, default='')
    logo_url = Column(Text)
    homepage_url = Column(Text)

    # Internal metrics
    install_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    tools_count = Column(Integer, default=0)

    # Status
    status = Column(String(20), default='approved')
    verification_status = Column(String(20), default='unverified')

    # Creator (denormalized for performance)
    creator_id = Column(String(36))
    creator_name = Column(Text)
    creator_username = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    markdown_contents = relationship("MarkdownContent", back_populates="server", cascade="all, delete-orphan")
    github_info = relationship("GithubInfo", back_populates="server", uselist=False, cascade="all, delete-orphan")
    npm_info = relationship("NpmInfo", back_populates="server", uselist=False, cascade="all, delete-orphan")
    mcp_config_npm = relationship("McpConfigNpm", back_populates="server", uselist=False, cascade="all, delete-orphan")
    mcp_config_docker = relationship("McpConfigDocker", back_populates="server", uselist=False, cascade="all, delete-orphan")
    tools = relationship("Tool", back_populates="server", cascade="all, delete-orphan")
    server_categories = relationship("ServerCategory", back_populates="server", cascade="all, delete-orphan")
    server_tags = relationship("ServerTag", back_populates="server", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('approved', 'pending', 'rejected')", name='check_status'),
        CheckConstraint("verification_status IN ('verified', 'unverified')", name='check_verification_status'),
    )

    def __repr__(self):
        return f"<Server(slug='{self.slug}', name='{self.name}')>"


class MarkdownContent(Base):
    """
    Markdown content sections (about, readme, faq, tools)
    """
    __tablename__ = 'markdown_content'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), nullable=False)

    # Content type
    content_type = Column(String(20), nullable=False)

    # Markdown content
    content = Column(Text, nullable=False)
    content_html = Column(Text)

    # Metadata
    word_count = Column(Integer)
    estimated_reading_time_minutes = Column(Integer)
    extracted_from = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    server = relationship("Server", back_populates="markdown_contents")

    # Constraints
    __table_args__ = (
        CheckConstraint("content_type IN ('about', 'readme', 'faq', 'tools')", name='check_content_type'),
        UniqueConstraint('server_id', 'content_type', name='uq_server_content_type'),
    )

    def __repr__(self):
        return f"<MarkdownContent(server_id={self.server_id}, type='{self.content_type}')>"


# ============================================================================
# External Info Models
# ============================================================================

class GithubInfo(Base):
    """
    Enhanced GitHub repository information with comprehensive stats
    """
    __tablename__ = 'github_info'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), unique=True, nullable=False)

    # URLs and identification
    github_url = Column(Text, nullable=False)
    github_owner = Column(Text, nullable=False)
    github_repo = Column(Text, nullable=False)
    github_full_name = Column(Text, nullable=False)  # "owner/repo"

    # Main metrics
    github_stars = Column(Integer, default=0)
    github_forks = Column(Integer, default=0)
    github_watchers = Column(Integer, default=0)
    github_open_issues = Column(Integer, default=0)

    # Activity
    github_last_commit = Column(DateTime)
    github_created_at = Column(DateTime)
    github_updated_at = Column(DateTime)
    commit_frequency = Column(Integer)  # commits in last 30 days

    # Project info
    github_description = Column(Text)
    primary_language = Column(Text)  # "TypeScript", "Python"
    languages = Column(Text)  # JSON: {"TypeScript": 89456, "JavaScript": 12345}
    github_topics = Column(Text)  # JSON array: ["mcp", "railway"]

    # License
    license = Column(Text)  # "mit", "apache-2.0"
    license_name = Column(Text)  # "MIT License"

    # Status
    is_archived = Column(Integer, default=0)  # Boolean as INTEGER
    is_fork = Column(Integer, default=0)
    is_disabled = Column(Integer, default=0)
    default_branch = Column(Text, default='main')

    # Release
    latest_github_version = Column(Text)
    latest_release_date = Column(DateTime)
    release_notes = Column(Text)
    is_prerelease = Column(Integer, default=0)

    # Community
    contributors_count = Column(Integer, default=0)
    top_contributors = Column(Text)  # JSON: [{"login": "user1", "contributions": 145}]

    # Project quality
    github_health_score = Column(Integer)  # 0-100
    has_readme = Column(Integer, default=1)
    has_license = Column(Integer, default=0)
    has_contributing = Column(Integer, default=0)
    has_code_of_conduct = Column(Integer, default=0)

    # Trending
    stars_last_week = Column(Integer, default=0)
    stars_last_month = Column(Integer, default=0)

    # README
    readme_size = Column(Integer)  # Size in bytes

    # Sync timestamps
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    server = relationship("Server", back_populates="github_info")

    # Hybrid properties for JSON fields
    @hybrid_property
    def languages_dict(self):
        """Get languages as Python dict"""
        return json.loads(self.languages) if self.languages else {}

    @languages_dict.setter
    def languages_dict(self, value):
        """Set languages from Python dict"""
        self.languages = json.dumps(value) if value else None

    @hybrid_property
    def topics_list(self):
        """Get topics as Python list"""
        return json.loads(self.github_topics) if self.github_topics else []

    @topics_list.setter
    def topics_list(self, value):
        """Set topics from Python list"""
        self.github_topics = json.dumps(value) if value else None

    @hybrid_property
    def contributors_list(self):
        """Get top contributors as Python list"""
        return json.loads(self.top_contributors) if self.top_contributors else []

    @contributors_list.setter
    def contributors_list(self, value):
        """Set top contributors from Python list"""
        self.top_contributors = json.dumps(value) if value else None

    def __repr__(self):
        return f"<GithubInfo({self.github_owner}/{self.github_repo} ⭐{self.github_stars})>"


class NpmInfo(Base):
    """
    npm package information
    """
    __tablename__ = 'npm_info'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Identification
    npm_package = Column(Text, nullable=False)
    npm_version = Column(Text, nullable=False)

    # Metrics
    npm_downloads_weekly = Column(Integer, default=0)
    npm_downloads_monthly = Column(Integer, default=0)

    # Metadata
    npm_license = Column(Text)
    npm_homepage = Column(Text)
    npm_repository_url = Column(Text)

    # Versions
    latest_version = Column(Text)
    latest_version_published_at = Column(DateTime)

    # Sync timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    server = relationship("Server", back_populates="npm_info")

    def __repr__(self):
        return f"<NpmInfo({self.npm_package}@{self.npm_version})>"


# ============================================================================
# MCP Configuration Models
# ============================================================================

class McpConfigNpm(Base):
    """
    NPM-based MCP server configuration
    """
    __tablename__ = 'mcp_config_npm'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Installation command
    command = Column(Text, nullable=False, default='npx')
    args = Column(Text, nullable=False)  # JSON array as string

    # Environment variables
    env_required = Column(Text, default='[]')  # JSON array as string
    env_descriptions = Column(Text, default='{}')  # JSON object as string

    # Metadata
    runtime = Column(Text, default='node')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    server = relationship("Server", back_populates="mcp_config_npm")

    # Constraints
    __table_args__ = (
        CheckConstraint("command IN ('npx', 'node', 'npm')", name='check_npm_command'),
    )

    @hybrid_property
    def args_list(self):
        """Get args as Python list"""
        return json.loads(self.args) if self.args else []

    @args_list.setter
    def args_list(self, value):
        """Set args from Python list"""
        self.args = json.dumps(value)

    @hybrid_property
    def env_required_list(self):
        """Get env_required as Python list"""
        return json.loads(self.env_required) if self.env_required else []

    @env_required_list.setter
    def env_required_list(self, value):
        """Set env_required from Python list"""
        self.env_required = json.dumps(value)

    @hybrid_property
    def env_descriptions_dict(self):
        """Get env_descriptions as Python dict"""
        return json.loads(self.env_descriptions) if self.env_descriptions else {}

    @env_descriptions_dict.setter
    def env_descriptions_dict(self, value):
        """Set env_descriptions from Python dict"""
        self.env_descriptions = json.dumps(value)

    def __repr__(self):
        return f"<McpConfigNpm(command='{self.command}')>"


class McpConfigDocker(Base):
    """
    Docker-based MCP server configuration
    """
    __tablename__ = 'mcp_config_docker'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Docker image
    docker_image = Column(Text, nullable=False)
    docker_tag = Column(Text, default='latest')

    # Docker command
    docker_command = Column(Text, default='[]')  # JSON array as string

    # Environment variables
    env_required = Column(Text, default='[]')  # JSON array as string
    env_descriptions = Column(Text, default='{}')  # JSON object as string

    # Ports and volumes
    ports = Column(Text, default='{}')  # JSON object as string
    volumes = Column(Text, default='{}')  # JSON object as string

    # Network configuration
    network_mode = Column(Text, default='bridge')

    # Metadata
    runtime = Column(Text, default='docker')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    server = relationship("Server", back_populates="mcp_config_docker")

    @hybrid_property
    def docker_command_list(self):
        """Get docker_command as Python list"""
        return json.loads(self.docker_command) if self.docker_command else []

    @docker_command_list.setter
    def docker_command_list(self, value):
        """Set docker_command from Python list"""
        self.docker_command = json.dumps(value)

    @hybrid_property
    def env_required_list(self):
        """Get env_required as Python list"""
        return json.loads(self.env_required) if self.env_required else []

    @env_required_list.setter
    def env_required_list(self, value):
        """Set env_required from Python list"""
        self.env_required = json.dumps(value)

    @hybrid_property
    def ports_dict(self):
        """Get ports as Python dict"""
        return json.loads(self.ports) if self.ports else {}

    @ports_dict.setter
    def ports_dict(self, value):
        """Set ports from Python dict"""
        self.ports = json.dumps(value)

    @hybrid_property
    def volumes_dict(self):
        """Get volumes as Python dict"""
        return json.loads(self.volumes) if self.volumes else {}

    @volumes_dict.setter
    def volumes_dict(self, value):
        """Set volumes from Python dict"""
        self.volumes = json.dumps(value)

    def __repr__(self):
        return f"<McpConfigDocker(image='{self.docker_image}')>"


# ============================================================================
# Tools Model
# ============================================================================

class Tool(Base):
    """
    Individual MCP tools provided by servers
    """
    __tablename__ = 'tools'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), nullable=False)

    # Identification
    name = Column(Text, nullable=False)
    display_name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    # Input schema (JSON Schema as TEXT)
    input_schema = Column(Text, nullable=False)

    # Examples
    example_usage = Column(Text)
    example_response = Column(Text)

    # Metadata
    category = Column(Text)
    is_dangerous = Column(Integer, default=0)  # Boolean as INTEGER
    requires_auth = Column(Integer, default=0)  # Boolean as INTEGER

    # Display order
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    server = relationship("Server", back_populates="tools")

    # Constraints
    __table_args__ = (
        UniqueConstraint('server_id', 'name', name='uq_server_tool_name'),
    )

    @hybrid_property
    def input_schema_dict(self):
        """Get input_schema as Python dict"""
        return json.loads(self.input_schema) if self.input_schema else {}

    @input_schema_dict.setter
    def input_schema_dict(self, value):
        """Set input_schema from Python dict"""
        self.input_schema = json.dumps(value)

    def __repr__(self):
        return f"<Tool(name='{self.name}')>"


class ToolParameter(Base):
    """
    Parameters for individual MCP tools
    """
    __tablename__ = 'tool_parameters'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tool_id = Column(String(36), ForeignKey('tools.id', ondelete='CASCADE'), nullable=False)

    # Parameter identification
    name = Column(Text, nullable=False)
    type = Column(Text)  # string, integer, boolean, array, object, number, null
    description = Column(Text)

    # Validation
    required = Column(Integer, default=0)  # Boolean as INTEGER (1=required, 0=optional)
    default_value = Column(Text)  # Stored as JSON string
    example_value = Column(Text)  # Stored as JSON string

    # Display order
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    tool = relationship("Tool", backref="parameters")

    # Constraints
    __table_args__ = (
        UniqueConstraint('tool_id', 'name', name='uq_tool_param_name'),
    )

    def __repr__(self):
        return f"<ToolParameter(name='{self.name}', type='{self.type}')>"


# ============================================================================
# Categories and Tags Models
# ============================================================================

class Category(Base):
    """
    Reusable categories for organizing servers
    """
    __tablename__ = 'categories'

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Identification
    slug = Column(String(255), unique=True, nullable=False)
    name = Column(Text, unique=True, nullable=False)

    # Description
    description = Column(Text)

    # Visual
    icon = Column(Text)
    color = Column(Text, default='#3B82F6')

    # Stats
    server_count = Column(Integer, default=0)

    # Display order
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server_categories = relationship("ServerCategory", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(slug='{self.slug}', name='{self.name}')>"


class Tag(Base):
    """
    Reusable tags for labeling servers
    """
    __tablename__ = 'tags'

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Identification
    slug = Column(String(255), unique=True, nullable=False)
    name = Column(Text, unique=True, nullable=False)

    # Description
    description = Column(Text)

    # Visual
    color = Column(Text, default='#3B82F6')

    # Stats
    server_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server_tags = relationship("ServerTag", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tag(slug='{self.slug}', name='{self.name}')>"


# ============================================================================
# Junction Tables (Many-to-Many)
# ============================================================================

class ServerCategory(Base):
    """
    Many-to-many relationship between servers and categories
    """
    __tablename__ = 'server_categories'

    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True)
    category_id = Column(String(36), ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)

    display_order = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = relationship("Server", back_populates="server_categories")
    category = relationship("Category", back_populates="server_categories")

    def __repr__(self):
        return f"<ServerCategory(server_id={self.server_id}, category_id={self.category_id})>"


class ServerTag(Base):
    """
    Many-to-many relationship between servers and tags
    """
    __tablename__ = 'server_tags'

    server_id = Column(String(36), ForeignKey('servers.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(String(36), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)

    display_order = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    server = relationship("Server", back_populates="server_tags")
    tag = relationship("Tag", back_populates="server_tags")

    def __repr__(self):
        return f"<ServerTag(server_id={self.server_id}, tag_id={self.tag_id})>"


# ============================================================================
# MCP.so URL Collection Table (Phase 1 & 2)
# ============================================================================

class McpSoServerUrl(Base):
    """
    Staging table for mcp.so server URL collection
    Phase 1: Collect URLs from pagination
    Phase 2: Extract GitHub links from each URL
    """
    __tablename__ = 'mcp_so_server_urls'

    # Primary identifier
    id = Column(String(36), primary_key=True, default=generate_uuid)

    # URL information (NOT unique to allow multiple servers per page)
    mcp_so_url = Column(Text, nullable=False, index=True)

    # Metadata extracted from URL
    server_name = Column(Text, nullable=False)
    owner_name = Column(Text)
    slug = Column(Text, nullable=False, index=True)

    # Phase 2 status tracking
    phase2_status = Column(String(20), default='pending')
    phase2_attempts = Column(Integer, default=0)
    phase2_last_attempt = Column(DateTime)
    phase2_error = Column(Text)

    # GitHub information (populated in Phase 2)
    github_url = Column(Text)
    github_owner = Column(Text)
    github_repo = Column(Text)

    # Collection metadata
    page_number = Column(Integer, index=True)
    priority = Column(Integer, default=0)

    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("phase2_status IN ('pending', 'processing', 'completed', 'failed')", name='check_phase2_status'),
        CheckConstraint("phase2_attempts >= 0", name='check_phase2_attempts'),
        CheckConstraint("priority >= 0", name='check_priority'),
    )

    def __repr__(self):
        return f"<McpSoServerUrl(slug='{self.slug}', status='{self.phase2_status}')>"
