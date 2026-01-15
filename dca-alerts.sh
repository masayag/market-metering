#!/bin/bash

# DCA Market Drop Alert Service Runner
# This script loads environment variables from .env and runs the service

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Run the DCA Market Drop Alert Service with environment configuration.

OPTIONS:
    -v, --verbose       Enable verbose (DEBUG) logging
    -c, --config FILE   Use additional YAML configuration file
    -n, --no-color      Disable colored console output
    -d, --dry-run       Validate configuration without running
    -h, --help          Show this help message

EXAMPLES:
    $0                          # Run with .env configuration
    $0 -v                       # Run with verbose logging
    $0 -c config/prod.yaml      # Run with additional YAML config
    $0 --dry-run                # Validate configuration only

ENVIRONMENT:
    Configuration is loaded from: $ENV_FILE
EOF
}

# Function to validate .env file
validate_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at: $ENV_FILE"
        print_info "Please copy .env.example to .env and configure your settings"
        return 1
    fi

    # Check for required environment variables
    local required_vars=(
        "DCA_SMTP_HOST"
        "DCA_SMTP_PORT"
        "DCA_SMTP_USER"
        "DCA_SMTP_PASSWORD"
        "DCA_SENDER_EMAIL"
        "DCA_RECIPIENT_EMAIL"
    )

    print_info "Validating .env configuration..."

    # Source the .env file to check variables
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Disable automatic export

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        return 1
    fi

    print_success "Environment configuration validated"
    return 0
}

# Function to check if Python environment is ready
check_python_env() {
    print_info "Checking Python environment..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        return 1
    fi

    # Check if virtual environment directory exists
    if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
        print_error "Virtual environment not found at $SCRIPT_DIR/.venv"
        print_info "Please create a virtual environment first:"
        print_info "  python3 -m venv .venv"
        print_info "  source .venv/bin/activate"
        print_info "  pip install -e \".[dev]\""
        return 1
    fi

    print_success "Found virtual environment at $SCRIPT_DIR/.venv"

    # Activate virtual environment for package check
    print_info "Activating virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"

    # Check if the package is installed
    if ! python -c "import dca_alerts" 2>/dev/null; then
        print_error "dca_alerts package is not installed in virtual environment"
        print_info "Please install the package first:"
        print_info "  source .venv/bin/activate"
        print_info "  pip install -e \".[dev]\""
        return 1
    fi

    print_success "Python environment ready with dca_alerts package"
    return 0
}

# Function to run the service
run_service() {
    local python_args=()
    local verbose=false
    local config_file=""
    local no_color=false
    local dry_run=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                verbose=true
                python_args+=("-v")
                shift
                ;;
            -c|--config)
                config_file="$2"
                python_args+=("-c" "$config_file")
                shift 2
                ;;
            -n|--no-color)
                no_color=true
                python_args+=("--no-color")
                shift
                ;;
            -d|--dry-run)
                dry_run=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Validate environment
    if ! validate_env_file; then
        exit 1
    fi

    # Check Python environment
    if ! check_python_env; then
        exit 1
    fi

    # If dry run, just validate and exit
    if [[ "$dry_run" == true ]]; then
        print_success "Configuration validation completed successfully"
        print_info "Service is ready to run with these settings:"
        echo "  - SMTP Host: ${DCA_SMTP_HOST}"
        echo "  - SMTP Port: ${DCA_SMTP_PORT}"
        echo "  - Sender: ${DCA_SENDER_EMAIL}"
        echo "  - Recipient: ${DCA_RECIPIENT_EMAIL}"
        echo "  - Drop Increment: ${DCA_DROP_INCREMENT}%"
        echo "  - Log Level: ${DCA_LOG_LEVEL}"
        echo "  - ATH Storage: ${DCA_ATH_STORAGE_PATH}"
        exit 0
    fi

    # Load environment variables
    set -a
    source "$ENV_FILE"
    set +a

    # Additional config file validation
    if [[ -n "$config_file" && ! -f "$config_file" ]]; then
        print_error "Configuration file not found: $config_file"
        exit 1
    fi

    # Create data directory if it doesn't exist
    local data_dir
    data_dir=$(dirname "${DCA_ATH_STORAGE_PATH}")
    if [[ ! -d "$data_dir" ]]; then
        print_info "Creating data directory: $data_dir"
        mkdir -p "$data_dir"
    fi

    # Run the service
    print_info "Starting DCA Market Drop Alert Service..."
    if [[ "$verbose" == true ]]; then
        print_info "Verbose logging enabled"
    fi
    if [[ "$no_color" == true ]]; then
        print_info "Colored output disabled"
    fi
    if [[ -n "$config_file" ]]; then
        print_info "Using additional config file: $config_file"
    fi

    echo
    print_success "Launching service with environment configuration from $ENV_FILE"
    echo

    # Execute the Python service (virtual environment already activated)
    if [[ ${#python_args[@]} -gt 0 ]]; then
        exec python -m dca_alerts.main "${python_args[@]}"
    else
        exec python -m dca_alerts.main
    fi
}

# Main execution
main() {
    print_info "DCA Market Drop Alert Service Runner"
    print_info "Working directory: $SCRIPT_DIR"
    echo

    # Run the service with all passed arguments
    run_service "$@"
}

# Execute main function with all script arguments
main "$@"