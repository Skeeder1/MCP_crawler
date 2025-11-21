"""
Configuration for mcp.so scraping with anti-detection measures
Includes random delays, varied user agents, and exponential backoff
"""
import random

# ============================================================================
# Anti-Detection Configuration
# ============================================================================

# User agents pool (rotate to avoid detection)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def get_random_user_agent():
    """Get a random user agent from the pool"""
    return random.choice(USER_AGENTS)


def get_random_delay(min_delay, max_delay):
    """
    Get a random delay between min and max (in seconds)
    Uses uniform distribution with slight randomness
    """
    base_delay = random.uniform(min_delay, max_delay)
    # Add micro-randomness (human-like)
    jitter = random.uniform(-0.2, 0.3)
    return max(0.5, base_delay + jitter)


# ============================================================================
# Phase 1: URL Collection Configuration
# ============================================================================

PHASE1_CONFIG = {
    # === TARGET CONFIGURATION ===
    'TARGET_URLS': 100,           # Number of URLs to collect (change to 10000 for scaling)
    'MAX_PAGES': 50,              # Maximum pages to scrape (change to 500 for scaling)

    # === DELAYS (Anti-Detection) ===
    'DELAY_BETWEEN_PAGES_MIN': 3.0,    # Minimum delay between pages (seconds)
    'DELAY_BETWEEN_PAGES_MAX': 7.0,    # Maximum delay between pages (seconds)
    'INITIAL_PAGE_WAIT': 5.0,          # Wait after loading first page (let JS render)
    'PAGE_LOAD_WAIT': 3.0,             # Wait for each page to load

    # === RETRY CONFIGURATION ===
    'MAX_PAGE_RETRIES': 3,        # Retry page load if fails
    'RETRY_DELAY_BASE': 5.0,      # Base delay for exponential backoff
    'RETRY_DELAY_MAX': 60.0,      # Maximum retry delay

    # === SCRAPING BEHAVIOR ===
    'BATCH_SIZE': 50,             # Number of URLs to insert per DB batch
    'EMPTY_PAGE_THRESHOLD': 3,    # Number of empty pages before stopping
    'HEADLESS': True,             # Run browser in headless mode
    'TIMEOUT': 30000,             # Page load timeout (ms)

    # === DETECTION AVOIDANCE ===
    'ROTATE_USER_AGENT': True,    # Rotate user agent per page
    'RANDOM_VIEWPORT': True,       # Randomize viewport size
    'SIMULATE_HUMAN': True,        # Add random mouse movements and scrolls
}

# ============================================================================
# Phase 2: GitHub Extraction Configuration
# ============================================================================

PHASE2_CONFIG = {
    # === PROCESSING ===
    'BATCH_SIZE': 10,             # Number of URLs to process per batch (change to 50 for scaling)
    'MAX_RETRIES': 3,             # Maximum retry attempts per URL

    # === DELAYS (Anti-Detection) ===
    'DELAY_BETWEEN_URLS_MIN': 2.0,     # Minimum delay between URLs (seconds)
    'DELAY_BETWEEN_URLS_MAX': 5.0,     # Maximum delay between URLs (seconds)
    'DELAY_BETWEEN_BATCHES_MIN': 10.0, # Minimum delay between batches
    'DELAY_BETWEEN_BATCHES_MAX': 20.0, # Maximum delay between batches
    'INITIAL_PAGE_WAIT': 4.0,          # Wait after loading first URL

    # === RETRY CONFIGURATION ===
    'RETRY_DELAY_BASE': 10.0,     # Base delay for exponential backoff
    'RETRY_DELAY_MAX': 120.0,     # Maximum retry delay (2 minutes)

    # === SCRAPING BEHAVIOR ===
    'HEADLESS': True,             # Run browser in headless mode
    'TIMEOUT': 30000,             # Page load timeout (ms)
    'PARALLEL_WORKERS': 1,        # Number of parallel workers (keep 1 for safety)

    # === DETECTION AVOIDANCE ===
    'ROTATE_USER_AGENT': True,    # Rotate user agent per URL
    'RANDOM_VIEWPORT': True,       # Randomize viewport size
    'SIMULATE_HUMAN': True,        # Add random mouse movements
}

# ============================================================================
# Viewport Sizes (for randomization)
# ============================================================================

VIEWPORT_SIZES = [
    {'width': 1920, 'height': 1080},  # Full HD
    {'width': 1366, 'height': 768},   # Common laptop
    {'width': 1536, 'height': 864},   # Laptop
    {'width': 1440, 'height': 900},   # MacBook
    {'width': 1280, 'height': 720},   # HD
]

def get_random_viewport():
    """Get a random viewport size"""
    return random.choice(VIEWPORT_SIZES)


# ============================================================================
# Exponential Backoff Calculator
# ============================================================================

def calculate_backoff_delay(attempt, base_delay, max_delay):
    """
    Calculate exponential backoff delay with jitter

    Args:
        attempt: Retry attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay cap

    Returns:
        float: Delay in seconds
    """
    # Exponential: delay = base * (2 ^ attempt)
    delay = base_delay * (2 ** attempt)

    # Cap at max
    delay = min(delay, max_delay)

    # Add jitter (±20%)
    jitter = delay * random.uniform(-0.2, 0.2)

    return delay + jitter


# ============================================================================
# Preset Scenarios for Scaling
# ============================================================================

SCENARIOS = {
    # Quick test (10 servers, fast)
    'dev': {
        'phase1': {
            'TARGET_URLS': 10,
            'MAX_PAGES': 2,
            'DELAY_BETWEEN_PAGES_MIN': 1.0,
            'DELAY_BETWEEN_PAGES_MAX': 2.0,
        },
        'phase2': {
            'BATCH_SIZE': 5,
            'DELAY_BETWEEN_URLS_MIN': 1.0,
            'DELAY_BETWEEN_URLS_MAX': 2.0,
            'DELAY_BETWEEN_BATCHES_MIN': 3.0,
            'DELAY_BETWEEN_BATCHES_MAX': 5.0,
        }
    },

    # Production (100 servers, balanced)
    'production_100': {
        'phase1': {
            'TARGET_URLS': 100,
            'MAX_PAGES': 10,
            'DELAY_BETWEEN_PAGES_MIN': 3.0,
            'DELAY_BETWEEN_PAGES_MAX': 7.0,
        },
        'phase2': {
            'BATCH_SIZE': 10,
            'DELAY_BETWEEN_URLS_MIN': 2.0,
            'DELAY_BETWEEN_URLS_MAX': 5.0,
            'DELAY_BETWEEN_BATCHES_MIN': 10.0,
            'DELAY_BETWEEN_BATCHES_MAX': 20.0,
        }
    },

    # Production (1000 servers, moderate)
    'production_1000': {
        'phase1': {
            'TARGET_URLS': 1000,
            'MAX_PAGES': 50,
            'DELAY_BETWEEN_PAGES_MIN': 2.0,
            'DELAY_BETWEEN_PAGES_MAX': 5.0,
        },
        'phase2': {
            'BATCH_SIZE': 20,
            'DELAY_BETWEEN_URLS_MIN': 1.5,
            'DELAY_BETWEEN_URLS_MAX': 4.0,
            'DELAY_BETWEEN_BATCHES_MIN': 8.0,
            'DELAY_BETWEEN_BATCHES_MAX': 15.0,
        }
    },

    # Production (10000 servers, aggressive but safe)
    'production_10000': {
        'phase1': {
            'TARGET_URLS': 10000,
            'MAX_PAGES': 500,
            'DELAY_BETWEEN_PAGES_MIN': 2.0,
            'DELAY_BETWEEN_PAGES_MAX': 4.0,
        },
        'phase2': {
            'BATCH_SIZE': 50,
            'DELAY_BETWEEN_URLS_MIN': 1.0,
            'DELAY_BETWEEN_URLS_MAX': 3.0,
            'DELAY_BETWEEN_BATCHES_MIN': 5.0,
            'DELAY_BETWEEN_BATCHES_MAX': 10.0,
            'PARALLEL_WORKERS': 2,  # Slightly more aggressive
        }
    },
}


def apply_scenario(scenario_name):
    """
    Apply a preset scenario configuration

    Args:
        scenario_name: One of 'dev', 'production_100', 'production_1000', 'production_10000'

    Returns:
        tuple: (phase1_config, phase2_config)
    """
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Choose from {list(SCENARIOS.keys())}")

    scenario = SCENARIOS[scenario_name]

    # Deep copy configs
    phase1 = PHASE1_CONFIG.copy()
    phase2 = PHASE2_CONFIG.copy()

    # Apply scenario overrides
    phase1.update(scenario['phase1'])
    phase2.update(scenario['phase2'])

    return phase1, phase2


# ============================================================================
# Estimated Time Calculator
# ============================================================================

def estimate_phase1_time(config):
    """Estimate Phase 1 execution time"""
    avg_delay = (config['DELAY_BETWEEN_PAGES_MIN'] + config['DELAY_BETWEEN_PAGES_MAX']) / 2
    page_time = avg_delay + config['PAGE_LOAD_WAIT']
    estimated_pages = min(config['MAX_PAGES'], config['TARGET_URLS'] // 20)  # Assume 20 URLs/page
    total_seconds = estimated_pages * page_time
    return total_seconds / 60  # Return in minutes


def estimate_phase2_time(config, num_urls):
    """Estimate Phase 2 execution time"""
    avg_url_delay = (config['DELAY_BETWEEN_URLS_MIN'] + config['DELAY_BETWEEN_URLS_MAX']) / 2
    avg_batch_delay = (config['DELAY_BETWEEN_BATCHES_MIN'] + config['DELAY_BETWEEN_BATCHES_MAX']) / 2

    url_time = avg_url_delay + 3.0  # 3s for scraping
    num_batches = (num_urls // config['BATCH_SIZE']) + 1

    total_seconds = (num_urls * url_time) + (num_batches * avg_batch_delay)
    return total_seconds / 60  # Return in minutes


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Configuration Scenarios")
    print("=" * 70)

    for scenario_name in SCENARIOS.keys():
        phase1, phase2 = apply_scenario(scenario_name)

        print(f"\n📊 Scenario: {scenario_name}")
        print(f"  Target URLs: {phase1['TARGET_URLS']}")
        print(f"  Phase 1 time: ~{estimate_phase1_time(phase1):.1f} minutes")
        print(f"  Phase 2 time: ~{estimate_phase2_time(phase2, phase1['TARGET_URLS']):.1f} minutes")
        print(f"  Total time: ~{estimate_phase1_time(phase1) + estimate_phase2_time(phase2, phase1['TARGET_URLS']):.1f} minutes")
