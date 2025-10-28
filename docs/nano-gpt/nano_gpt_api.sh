#!/bin/bash

# =============================================================================
# NanoGPT Image Generation Script - Cleaned Version
# =============================================================================
# This script sends images to the NanoGPT API for generation and handles the
# response by decoding base64 images and saving them with proper naming.
#
# Features:
# - Base64 response trimming to prevent terminal overload
# - Automatic image format detection
# - File naming: waifu-{YYYY-MM-DD}-{UUID}.{ext}
# - Cross-platform compatibility (Linux/macOS)
# - Robust error handling and fallbacks
# =============================================================================

# -----------------------------------------------------------------------------
# SCRIPT CONSTANTS
# -----------------------------------------------------------------------------
# Add this near the top with other constants
DEBUG_MODE="${DEBUG_MODE:-1}"  # Set to 0 to disable debug mode

DEFAULT_CONFIG_FILE="${CONFIG_FILE:-./nano_gpt_config.conf}"
DEFAULT_API_URL="https://nano-gpt.com/v1/images/generations"
DEFAULT_MODEL="seedream-v4"
DEFAULT_SIZE="1024x1024"
DEFAULT_RESPONSE_FORMAT="b64_json"
DEFAULT_N=1

# File naming constants
FILENAME_PREFIX="waifu"
UUID_LENGTH=8
DEFAULT_IMAGE_EXT="jpg"

# Display constants
MAX_DISPLAY_LENGTH=100
TRIM_PREFIX_LENGTH=$((MAX_DISPLAY_LENGTH / 2 - 5))
TRIM_SUFFIX_LENGTH=$((MAX_DISPLAY_LENGTH / 2 - 5))

# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS - String and Data Operations
# -----------------------------------------------------------------------------

# Generate 8-character UUID with fallbacks
# Returns: 8-character lowercase hexadecimal string
generate_uuid8() {
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr -d '-' | cut -c1-${UUID_LENGTH} | tr '[:upper:]' '[:lower:]'
    else
        # Fallback: use /dev/urandom
        cat /dev/urandom | tr -dc 'a-f0-9' | fold -w ${UUID_LENGTH} | head -n 1
    fi
}

# Get current date in YYYY-MM-DD format
# Returns: Current date string
get_date() {
    date +%Y-%m-%d
}

# Convert string to lowercase (cross-platform compatible)
# Args: $1 - String to convert
# Returns: Lowercase string
to_lowercase() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

# Trim base64 data URL for display to prevent terminal overload
# Args: $1 - Data URL to trim, $2 - Maximum length (optional, defaults to 100)
# Returns: Trimmed data URL with ellipsis
trim_data_url() {
    local data_url="$1"
    local max_length="${2:-$MAX_DISPLAY_LENGTH}"
    
    if [ ${#data_url} -le "$max_length" ]; then
        echo "$data_url"
    else
        local prefix
        prefix=$(echo "$data_url" | cut -c1-${TRIM_PREFIX_LENGTH})
        local suffix
        suffix=$(echo "$data_url" | rev | cut -c1-${TRIM_SUFFIX_LENGTH} | rev)
        echo "${prefix}...${suffix}"
    fi
}

# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS - Image Processing
# -----------------------------------------------------------------------------

# Detect image format from base64 data by checking magic numbers
# Args: $1 - Base64 encoded image data
# Returns: Image format (jpg, png, gif, webp, or jpg as default)
detect_image_format() {
    local base64_data="$1"
    # Decode just the first few bytes to check the magic number
    local header
    header=$(echo "$base64_data" | head -c 100 | base64 -d 2>/dev/null | hexdump -C | head -n 3)
    
    if echo "$header" | grep -q "ff d8 ff"; then
        echo "jpg"
    elif echo "$header" | grep -q "89 50 4e 47"; then
        echo "png"
    elif echo "$header" | grep -q "47 49 46 38"; then
        echo "gif"
    elif echo "$header" | grep -q "52 49 46 46.*57 45 42 50"; then
        echo "webp"
    else
        # Default to jpg if we can't detect
        echo "jpg"
    fi
}

# Decode base64 data URL to image file with proper naming
# Args: $1 - Data URL, $2 - Output directory (optional, defaults to current)
# Returns: Filepath of saved image on success, 1 on failure
decode_base64_image() {
    local data_url="$1"
    local output_dir="${2:-.}"
    
    # Extract base64 data from data URL (remove data:image/type;base64, prefix)
    local base64_data
    base64_data=$(echo "$data_url" | sed 's/^data:image\/[^;]*;base64,//')
    
    if [ -z "$base64_data" ]; then
        echo "Error: Invalid data URL format" >&2
        return 1
    fi
    
    # Detect image format
    local format
    format=$(detect_image_format "$base64_data")
    
    # Generate filename using waifu-{YYYY-MM-DD}-{UUID}.{ext} convention
    local date_str
    date_str=$(get_date)
    local uuid8
    uuid8=$(generate_uuid8)
    local filename="${FILENAME_PREFIX}-${date_str}-${uuid8}.${format}"
    local filepath="${output_dir}/${filename}"
    
    echo "Decoding image to: $filepath" >&2
    
    # Decode base64 to image file
    if echo "$base64_data" | base64 -d > "$filepath" 2>/dev/null; then
        echo "✓ Image saved: $filename" >&2
        echo "$filepath"  # Return the filepath
        return 0
    else
        echo "Error: Failed to decode base64 image data" >&2
        return 1
    fi
}

# Get MIME type for file based on extension with fallback detection
# Args: $1 - File path
# Returns: MIME type string
get_mime_type() {
    local file="$1"
    local lowercase_file
    lowercase_file=$(to_lowercase "$file")
    
    case "$lowercase_file" in
        *.jpg|*.jpeg) echo "image/jpeg" ;;
        *.png) echo "image/png" ;;
        *.gif) echo "image/gif" ;;
        *.webp) echo "image/webp" ;;
        *.bmp) echo "image/bmp" ;;
        *) 
            # Try to detect MIME type using file command
            if command -v file >/dev/null 2>&1; then
                file -b --mime-type "$file" 2>/dev/null || echo "image/jpeg"
            else
                echo "image/jpeg"
            fi
            ;;
    esac
}

# -----------------------------------------------------------------------------
# UTILITY FUNCTIONS - Base64 and Encoding
# -----------------------------------------------------------------------------

# Encode file to base64 with cross-platform compatibility
# Args: $1 - File path
# Returns: Base64 encoded data to stdout
encode_base64() {
    local file="$1"
    
    # Try different base64 command variations
    if base64 -w 0 "$file" 2>/dev/null; then
        # GNU coreutils version (Linux)
        return 0
    elif base64 -b 0 "$file" 2>/dev/null; then
        # BSD version (macOS)
        return 0
    elif base64 < "$file" | tr -d '\n'; then
        # Fallback: encode and remove newlines
        return 0
    else
        echo "Error: Unable to base64 encode file: $file" >&2
        return 1
    fi
}

# Create data URL with base64 encoding
# Args: $1 - Image file path
# Returns: Data URL string on success, 1 on failure
create_data_url() {
    local image_file="$1"
    local mime_type
    mime_type=$(get_mime_type "$image_file")
    local base64_data
    
    echo "Encoding $image_file..." >&2
    
    # Get base64 data using the compatible function
    base64_data=$(encode_base64 "$image_file")
    
    if [ -z "$base64_data" ]; then
        echo "Error: Failed to encode $image_file to base64" >&2
        return 1
    fi
    
    echo "data:${mime_type};base64,${base64_data}"
}

# -----------------------------------------------------------------------------
# CONFIGURATION MANAGEMENT
# -----------------------------------------------------------------------------

# Load configuration from file with validation
# Args: $1 - Config file path
load_config() {
    local config_file="$1"
    
    if [ ! -f "$config_file" ]; then
        echo "Warning: Config file '$config_file' not found. Creating default config..."
        create_default_config "$config_file"
        echo "Please edit '$config_file' and run the script again."
        exit 1
    fi
    
    echo "Loading configuration from: $config_file"
    
    # Source the config file in a subshell to avoid polluting current environment
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue
        
        # Remove leading/trailing whitespace and quotes
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//;s/^"//;s/"$//')
        
        case "$key" in
            API_KEY) API_KEY="$value" ;;
            API_URL) API_URL="$value" ;;
            MODEL) MODEL="$value" ;;
            PROMPT) PROMPT="$value" ;;
            SIZE) SIZE="$value" ;;
            RESPONSE_FORMAT) RESPONSE_FORMAT="$value" ;;
            N) N="$value" ;;
            *) : ;; # Ignore unknown keys
        esac
    done < "$config_file"
    
    # Validate required fields
    if [ -z "$API_KEY" ]; then
        echo "Error: API_KEY not set in config file or environment" >&2
        exit 1
    fi
    
    if [ -z "$PROMPT" ]; then
        echo "Error: PROMPT not set in config file" >&2
        exit 1
    fi
    
    echo "✓ Configuration loaded successfully" >&2
    echo "  Model: $MODEL" >&2
    echo "  Size: $SIZE" >&2
    echo "  Prompt: ${PROMPT:0:50}$([ ${#PROMPT} -gt 50 ] && echo '...')" >&2
}

# Create default configuration file
# Args: $1 - Config file path
create_default_config() {
    local config_file="$1"
    
    cat > "$config_file" <<EOF
# Nano GPT Image Generation Configuration
# Lines starting with # are comments

# Your API key (required)
API_KEY=your-api-key-here

# API endpoint (optional - uses default if not specified)
API_URL=https://nano-gpt.com/v1/images/generations

# Model to use (optional - uses default if not specified)
MODEL=google:4@1

# Main prompt for image generation (required)
PROMPT=Generate a high-quality artistic image based on the provided reference images

# Image generation parameters (optional)
SIZE=1024x1024
RESPONSE_FORMAT=url
N=1

# Example prompts you can use:
# PROMPT=Transform the user photo into an anime-style character
# PROMPT=Create a professional headshot based on the reference image
# PROMPT=Generate artistic variations of the provided images
# PROMPT=Apply cinematic lighting and effects to the base image
EOF
}

# -----------------------------------------------------------------------------
# JSON AND API UTILITIES
# -----------------------------------------------------------------------------

# Escape JSON strings properly for safe inclusion in JSON
# Args: $1 - String to escape
# Returns: Escaped string
escape_json_string() {
    local input="$1"
    # Escape backslashes, quotes, and control characters for JSON
    echo "$input" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\r/\\r/g; s/\n/\\n/g'
}

# Create JSON payload file to avoid argument list too long error
# Args: $1 - Temp file path, $2 - User photo, $3+ - Additional images
create_json_payload() {
    local temp_file="$1"
    local user_photo="$2"
    shift 2
    local additional_images=("$@")
    
    # Start writing JSON to temp file
    cat > "$temp_file" <<EOF
{
  "model": "$(escape_json_string "$MODEL")",
  "prompt": "$(escape_json_string "$PROMPT")",
  "n": $N,
  "size": "$(escape_json_string "$SIZE")",
  "response_format": "$(escape_json_string "$RESPONSE_FORMAT")",
  "imageDataUrls": [
EOF
    
    local first=true
    
    # First image: user-submitted photo
    if [ -f "$user_photo" ]; then
        echo "Processing user photo: $user_photo" >&2
        local data_url
        data_url=$(create_data_url "$user_photo")
        
        if [ -n "$data_url" ]; then
            # Escape the data URL for JSON
            local escaped_url
            escaped_url=$(escape_json_string "$data_url")
            printf '    "%s"' "$escaped_url" >> "$temp_file"
            first=false
        else
            echo "Warning: Failed to process user photo: $user_photo" >&2
        fi
    fi
    
    # Additional images in the order provided
    for img in "${additional_images[@]}"; do
        if [ -f "$img" ]; then
            echo "Processing additional image: $img" >&2
            local data_url
            data_url=$(create_data_url "$img")
            if [ -n "$data_url" ]; then  # Simply check if not empty
                if [ "$first" = false ]; then
                    echo "," >> "$temp_file"
                fi
                # Escape the data URL for JSON
                local escaped_url
                escaped_url=$(escape_json_string "$data_url")
                printf '    "%s"' "$escaped_url" >> "$temp_file"
                first=false
            else
                echo "Warning: Failed to process image: $img" >&2
            fi
        else
            echo "Warning: Image file not found: $img" >&2
        fi
    done

    # Close JSON structure
    cat >> "$temp_file" <<EOF

  ]
}
EOF
    
    echo "JSON payload written to: $temp_file" >&2
}

# -----------------------------------------------------------------------------
# RESPONSE PROCESSING
# -----------------------------------------------------------------------------

# Extract image data from JSON response with multiple format support
# Args: $1 - Response body
# Returns: List of image URLs/data URLs, one per line

extract_image_data_from_response() {
    local response_body="$1"

    echo "Debug: Full response structure (first 200 chars):" >&2
    printf '%s' "$response_body" | head -c 200 >&2
    echo -e "\n..." >&2

    # Check if it's valid JSON
    if echo "$response_body" | jq empty 2>/dev/null; then
        echo "Valid JSON with $(echo "$response_body" | jq '.data | length' 2>/dev/null) data items" >&2
    fi

    echo "Debug: Attempting to extract image data from response" >&2

    if command -v jq >/dev/null 2>&1; then
        echo "Debug: Using jq for JSON parsing" >&2

        # Use a single jq command to handle both cases
        local images
        images=$(echo "$response_body" | jq -r '
            .data[]? | 
            if .url then .url
            elif .b64_json then
                if (.b64_json | startswith("/9j/")) then "data:image/jpeg;base64," + .b64_json
                elif (.b64_json | startswith("iVBORw0")) then "data:image/png;base64," + .b64_json  
                elif (.b64_json | startswith("R0lGOD")) then "data:image/gif;base64," + .b64_json
                else "data:image/jpeg;base64," + .b64_json
                end
            else empty
            end
        ' 2>/dev/null)

        if [ -n "$images" ]; then
            local count
            count=$(echo "$images" | wc -l)
            echo "Debug: Found images: $count items" >&2
            echo "$images"
            return 0
        fi
    fi

    echo "Debug: No images found" >&2
    return 1
}

# Handle base64 image data by decoding and saving
# Args: $1 - Base64 data URL, $2 - Image number, $3 - Output directory
handle_base64_image() {
    local data_url="$1"
    local image_num="$2"
    local output_dir="$3"
    
    echo "Image $image_num:"
    echo "  Data URL preview: $(trim_data_url "$data_url" 80)"
    
    # Decode and save the image
    local saved_file
    saved_file=$(decode_base64_image "$data_url" "$output_dir")
    echo "Saved to: $saved_file"

    if [[ -n "$saved_file" ]]; then
        echo "  ✓ Saved as: $(basename "$saved_file")"
        echo "  📍 Location: $saved_file"
    else
        echo "  The file didn't save."
    fi
}

# Handle URL image data by downloading and saving
# Args: $1 - Image URL, $2 - Image number, $3 - Output directory
handle_url_image() {
    local image_url="$1"
    local image_num="$2"
    local output_dir="$3"
    
    echo "Image $image_num URL: $image_url"
    
    # Generate filename for downloaded image
    local date_str
    date_str=$(get_date)
    local uuid8
    uuid8=$(generate_uuid8)
    local filename="${FILENAME_PREFIX}-${date_str}-${uuid8}.${DEFAULT_IMAGE_EXT}"
    local filepath="${output_dir}/${filename}"
    
    echo "  Downloading to: $filename" >&2
    if curl -s -o "$filepath" "$image_url"; then
        echo "  ✓ Downloaded: $filename"
    else
        echo "  ✗ Failed to download image"
    fi
}

# Download image from URL with error handling
# Args: $1 - Image URL, $2 - Output file path
# Returns: 0 on success, 1 on failure
download_image_from_url() {
    local image_url="$1"
    local output_file="$2"
    
    if curl -s -o "$output_file" "$image_url"; then
        return 0
    else
        echo "Error: Failed to download image from $image_url" >&2
        return 1
    fi
}

# Process API response and handle all images found
# Args: $1 - Response body, $2 - Output directory (optional, defaults to current)
process_api_response() {
    local process_result
    process_result=$?

    local response_body="$1"
    local output_dir="${2:-.}"

    echo "" >&2
    echo "Cleaning up payload file: $payload_file" >&2
    rm -f "$payload_file"

    if [ "$DEBUG_MODE" = "1" ]; then
        echo "Debug: Debug mode enabled, keeping response file: $response_file" >&2
    else
        if [ $process_result -eq 0 ]; then
            rm -f "$response_file"
            echo "Debug: Response file cleaned up" >&2
        else
            echo "Debug: Image processing failed, keeping response file: $response_file" >&2
        fi
    fi
    
    echo "Processing API response..." >&2
        # Add this debug section
    echo "Debug: Response contains ${#response_body} characters" >&2
    echo "Debug: Looking for base64 data..." >&2

    # Extract image data from response
    local images
    images=$(extract_image_data_from_response "$response_body")
    local extract_result=$?

    echo "Debug: extract_image_data_from_response returned: $extract_result" >&2
    echo "Debug: Images found: $(echo "$images" | wc -l) lines" >&2
    
    if [ "$extract_result" -eq 0 ] && [ -n "$images" ]; then
        local count=1
        echo "$images" | while IFS= read -r image_data; do
            echo "Debug: Processing image $count, data length: ${#image_data}" >&2
            if [[ "$image_data" == data:image/* ]]; then
                echo "Debug: Found base64 data URL for image $count" >&2
                handle_base64_image "$image_data" "$count" "$output_dir"
            elif [[ "$image_data" == http* ]]; then
                echo "Debug: Found HTTP URL for image $count" >&2
                handle_url_image "$image_data" "$count" "$output_dir"
            else
                echo "Debug: Unknown image data format for image $count: ${image_data:0:50}..." >&2
            fi
            count=$((count + 1))
        done
        return 0  # Make sure to return success
    else
        echo "No image data found in response" >&2
        echo "Debug: Showing full API response:" >&2
        echo "----------------------------------------" >&2
        echo "$response_body" >&2
        echo "----------------------------------------" >&2
        echo "" >&2
        
        # Try to show response structure with jq if available
        if command -v jq >/dev/null 2>&1; then
            echo "Response structure (jq):" >&2
            echo "$response_body" | jq 'keys' 2>/dev/null || echo "Failed to parse with jq" >&2
        fi
    fi
}

# -----------------------------------------------------------------------------
# MAIN API FUNCTION
# -----------------------------------------------------------------------------

# Send generation request to API and process response
# Args: $1 - User photo, $2+ - Additional images
send_generation_request() {
    local user_photo="$1"
    shift
    local additional_images=("$@")
    
    echo "Building request with images in order:" >&2
    echo "1. User photo: $user_photo" >&2
    local i=2
    for img in "${additional_images[@]}"; do
        if [ -f "$img" ]; then
            echo "$i. Additional: $img" >&2
            i=$((i + 1))
        fi
    done
    echo "" >&2
    echo "Using prompt: $PROMPT" >&2
    echo "" >&2
    
    # Create JSON payload file in current working directory
    local payload_file
    payload_file="nano_gpt_payload_$(date +%s).json"
    
    echo "Creating JSON payload in current directory: $payload_file" >&2
    
    # Create the JSON payload in the file
    create_json_payload "$payload_file" "$user_photo" "${additional_images[@]}" || {
        echo "Error: Failed to create JSON payload." >&2;
        exit 1;
    }
    
    echo "JSON payload created: $payload_file" >&2
    echo "Payload size: $(wc -c < "$payload_file") bytes" >&2
    
    echo "Sending request to API..." >&2
    
    # Send the request using the payload file
    local response
    response=$(curl -s -w "\\n%{http_code}" \
        --request POST \
        --url "$API_URL" \
        --header "Authorization: Bearer $API_KEY" \
        --header "Content-Type: application/json" \
        --data @"$payload_file")
    
    # Extract HTTP status and response body
    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')
    
    # Handle response
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        echo "✓ Request successful (HTTP $http_code)!" >&2
        echo "" >&2
        
        # Save response to file for debugging
        local response_file
        response_file="api_response_$(date +%s).json"
        echo "$body" > "$response_file"
        echo "Debug: API response saved to: $response_file" >&2
        echo "" >&2
        
        process_api_response "$body" # Process and save images
        local process_results=$?

        echo "" >&2
        echo "Cleaning up payload file: $payload_file" >&2
        rm -f "$payload_file"
        
        # Clean up response file only if images were processed successfully
        if [ "$process_results" -eq 0 ]; then
            echo "Debug: Image processing successful, keeping response file for now" >&2
            # rm -f "$response_file"  # Comment this out for debugging
        else
            echo "Debug: Image processing failed, keeping response file: $response_file" >&2
        fi
        echo "Debug: Response file kept for debugging: $response_file" >&2
    else
        echo "✗ Request failed (HTTP $http_code)" >&2
        echo "Error response: $body" >&2
        echo "Keeping payload file for debugging: $payload_file" >&2
        return 1
    fi
}

# -----------------------------------------------------------------------------
# USAGE AND MAIN FUNCTION
# -----------------------------------------------------------------------------

# Show usage information with examples
show_usage() {
    cat <<EOF
Usage: $0 <user_photo> [additional_images...]

Arguments:
  user_photo         Primary user-submitted photo (required, goes first)
  additional_images  Additional reference images (optional)

Configuration:
  The prompt and other settings are loaded from: $DEFAULT_CONFIG_FILE
  Use CONFIG_FILE environment variable to specify a different config file.

Environment Variables:
  CONFIG_FILE       Path to configuration file (default: ./nano_gpt_config.conf)
  NANO_GPT_API_KEY  API key (overrides config file setting)

Examples:
  $0 user_selfie.jpg reference1.png reference2.jpg
  $0 photo.png
  
  # Using custom config file
  CONFIG_FILE=/path/to/my_custom_config.txt $0 user_photo.jpg style_ref.png

  # Override API Key via Environment
  export NANO_GPT_API_KEY="sk-another-key"
  $0 user_photo.jpg

Configuration File Format:
  The config file should contain key=value pairs:
  
  API_KEY=your-actual-api-key
  PROMPT=Transform the user photo into an anime-style character
  MODEL=google:4@1
  SIZE=1024x1024

EOF
}

# Main script execution with proper validation
main() {
    # Initialize variables with defaults
    API_URL="$DEFAULT_API_URL"
    API_KEY="${NANO_GPT_API_KEY}"
    MODEL="$DEFAULT_MODEL"
    SIZE="$DEFAULT_SIZE"
    RESPONSE_FORMAT="$DEFAULT_RESPONSE_FORMAT"
    N="$DEFAULT_N"
    PROMPT=""
    
    # Check if jq is available (optional but recommended)
    if ! command -v jq >/dev/null 2>&1; then
        echo "Warning: jq not found. JSON output processing might be limited." >&2
    fi
    
    # Load configuration first
    load_config "$DEFAULT_CONFIG_FILE"
    
    # Validate arguments
    if [ $# -lt 1 ]; then
        echo "Error: Please provide at least the user photo" >&2
        show_usage
        exit 1
    fi
    
    local user_photo="$1"
    shift
    local additional_images=("$@")
    
    # Validate user photo exists
    if [ ! -f "$user_photo" ]; then
        echo "Error: User photo '$user_photo' not found" >&2
        exit 1
    fi
    
    # Validate additional images exist
    for img in "${additional_images[@]}"; do
        if [ ! -f "$img" ]; then
            echo "Warning: Additional image '$img' not found, skipping" >&2
        fi
    done
    
    # Send the request
    send_generation_request "$user_photo" "${additional_images[@]}"
}

# -----------------------------------------------------------------------------
# SCRIPT EXECUTION
# -----------------------------------------------------------------------------

# Run main function with all arguments
main "$@"