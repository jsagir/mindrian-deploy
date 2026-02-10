#!/bin/bash
# @parseArger-begin
# @parseArger-help "eric - Generic AI Orchestration Script for Multi-Step Project Implementation" --option "help" --short-option "h"
# @parseArger-version "1.0.0" --option "version" --short-option "v"
# @parseArger-verbose --option "verbose" --level "0" --quiet-option "quiet"
_has_colors=0
if [ -t 1 ]; then # Check if stdout is a terminal
    ncolors=$(tput colors 2>/dev/null)
    if [ -n "$ncolors" ] && [ "$ncolors" -ge 8 ]; then
        _has_colors=1
    fi
fi
# @parseArger-declarations
# @parseArger pos plans-dir "Directory containing numbered plan files (01-*.md, 02-*.md, etc.)" --complete "directory"
# @parseArger opt prds-dir "Directory containing PRD files (same names as plan files)" --complete "directory"
# @parseArger opt vision "Path to vision document" --complete "file"
# @parseArger opt project-name "Project name for prompts and display" --default-value "this project"
# @parseArger opt start "Step number to start from" --short s --default-value "1"
# @parseArger opt end "Step number to end at (default: auto-detect from plans)" --short e
# @parseArger opt harness "AI harness to use" --short H --default-value "opencode" --one-of "opencode" --one-of "claude" --one-of "gemini" --one-of "codex" --one-of "kilo"
# @parseArger opt model "Model to use (default: zai-coding-plan/glm-4.7 for opencode, harness default for others)" --short m
# @parseArger opt validation-cmd "Validation command to run (repeatable)" --repeat
# @parseArger opt review-model "Model for final review phase"
# @parseArger opt review-output-dir "Output directory for review files" --default-value ".task-o-matic/review" --complete "directory"
# @parseArger opt review-harness "AI harness for final review phase" --one-of "opencode" --one-of "claude" --one-of "gemini" --one-of "codex" --one-of "kilo"
# @parseArger flag resume "Resume from last failed step"
# @parseArger flag dry-run "Show commands without executing" --short n
# @parseArger flag skip-commit "Skip automatic commits between steps"
# @parseArger flag skip-push "Skip automatic push after commits"
# @parseArger-declarations-end

# @parseArger-utils
_helpHasBeenPrinted=1;
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)";
# @parseArger-utils-end

# @parseArger-parsing

__cli_arg_count=$#;

die()
{
    local _ret=1
    if [[ -n "$2" ]] && [[ "$2" =~ ^[0-9]+$ ]]; then
       _ret="$2"
    fi
    test "${_PRINT_HELP:-no}" = yes && print_help >&2
    log "$1" -3 >&2
    exit "${_ret}"
}


begins_with_short_option()
{
    local first_option all_short_options=''
    first_option="${1:0:1}"
    test "$all_short_options" = "${all_short_options/$first_option/}" && return 1 || return 0
}

# POSITIONALS ARGUMENTS
_positionals=();
_optional_positionals=();
_arg_plans_dir="";
# OPTIONALS ARGUMENTS
_arg_prds_dir=
_arg_vision=
_arg_project_name="this project"
_arg_start="1"
_arg_end=
_arg_harness="opencode"
_one_of_arg_harness=("opencode" "claude" "gemini" "codex" "kilo" );
_arg_model=
_arg_validation_cmd=()
_arg_review_model=
_arg_review_output_dir=".task-o-matic/review"
_arg_review_harness=
_one_of_arg_review_harness=("opencode" "claude" "gemini" "codex" "kilo" );
# FLAGS
_arg_resume="off"
_arg_dry_run="off"
_arg_skip_commit="off"
_arg_skip_push="off"
# NESTED
_verbose_level="0";



print_help()
{
    _triggerSCHelp=1;

    if [[ "$_helpHasBeenPrinted" == "1" ]]; then
        _helpHasBeenPrinted=0;
        echo -e "eric - Generic AI Orchestration Script for Multi-Step Project Implementation:"
    echo -e "    plans-dir: Directory containing numbered plan files (01-*.md, 02-*.md, etc.)"
    echo -e "    --prds-dir <prds-dir>: Directory containing PRD files (same names as plan files)"
    echo -e "    --vision <vision>: Path to vision document"
    echo -e "    --project-name <project-name>: Project name for prompts and display [default: ' this project ']"
    echo -e "    -s, --start <start>: Step number to start from [default: ' 1 ']"
    echo -e "    -e, --end <end>: Step number to end at (default: auto-detect from plans)"
    echo -e "    -H, --harness <harness>: AI harness to use [default: ' opencode '] [one of 'opencode' 'claude' 'gemini' 'codex' 'kilo']"
    echo -e "    -m, --model <model>: Model to use (default: zai-coding-plan/glm-4.7 for opencode, harness default for others)"
    echo -e "    --validation-cmd <validation-cmd>: Validation command to run (repeatable), repeatable"
    echo -e "    --review-model <review-model>: Model for final review phase"
    echo -e "    --review-output-dir <review-output-dir>: Output directory for review files [default: ' .task-o-matic/review ']"
    echo -e "    --review-harness <review-harness>: AI harness for final review phase [one of 'opencode' 'claude' 'gemini' 'codex' 'kilo']"
    echo -e "    --resume|--no-resume: Resume from last failed step"
    echo -e "    -n|--dry-run|--no-dry-run: Show commands without executing"
    echo -e "    --skip-commit|--no-skip-commit: Skip automatic commits between steps"
    echo -e "    --skip-push|--no-skip-push: Skip automatic push after commits"
    echo -e "Usage :"
    echo -e "    $0 <plans-dir> [--prds-dir <value>] [--vision <value>] [--project-name <value>] [--start <value>] [--end <value>] [--harness <value>] [--model <value>] [--validation-cmd <value>] [--review-model <value>] [--review-output-dir <value>] [--review-harness <value>] [--[no-]resume] [--[no-]dry-run] [--[no-]skip-commit] [--[no-]skip-push]";
    fi

}

log() {
    local _arg_msg="${1}";
    local _arg_level="${2:-0}";
    if [ "${_arg_level}" -le "${_verbose_level}" ]; then
        case "$_arg_level" in
            -3)
                _arg_COLOR="\033[0;31m";
                ;;
            -2)
                _arg_COLOR="\033[0;33m";
                ;;
            -1)
                _arg_COLOR="\033[1;33m";
                ;;
            1)
                _arg_COLOR="\033[0;32m";
                ;;
            2)
                _arg_COLOR="\033[1;36m";
                ;;
            3)
                _arg_COLOR="\033[0;36m";
                ;;
            *)
                _arg_COLOR="\033[0m";
                ;;
        esac
        if [ "${_has_colors}" == "1" ]; then
            echo -e "${_arg_COLOR}${_arg_msg}\033[0m";
        else
            echo "${_arg_msg}";
        fi
    fi
}

parse_commandline()
{
    _positionals_count=0
    while test $# -gt 0
    do
        _key="$1"
        case "$_key" in
            --prds-dir)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_prds_dir="$2"
                shift
                ;;
            --prds-dir=*)
                _arg_prds_dir="${_key##--prds-dir=}"
                ;;

            --vision)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_vision="$2"
                shift
                ;;
            --vision=*)
                _arg_vision="${_key##--vision=}"
                ;;

            --project-name)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_project_name="$2"
                shift
                ;;
            --project-name=*)
                _arg_project_name="${_key##--project-name=}"
                ;;

            -s|--start)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_start="$2"
                shift
                ;;
            --start=*)
                _arg_start="${_key##--start=}"
                ;;
            -s*)
                _arg_start="${_key##-s}"
                ;;

            -e|--end)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_end="$2"
                shift
                ;;
            --end=*)
                _arg_end="${_key##--end=}"
                ;;
            -e*)
                _arg_end="${_key##-e}"
                ;;

            -H|--harness)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_harness="$2"
                if [[ "${#_one_of_arg_harness[@]}" -gt 0 ]];then [[ "${_one_of_arg_harness[*]}" =~ (^|[[:space:]])"$_arg_harness"($|[[:space:]]) ]] || die "harness must be one of: opencode claude gemini codex kilo";fi
                shift
                ;;
            --harness=*)
                _arg_harness="${_key##--harness=}"
                if [[ "${#_one_of_arg_harness[@]}" -gt 0 ]];then [[ "${_one_of_arg_harness[*]}" =~ (^|[[:space:]])"$_arg_harness"($|[[:space:]]) ]] || die "harness must be one of: opencode claude gemini codex kilo";fi
                ;;
            -H*)
                _arg_harness="${_key##-H}"
                if [[ "${#_one_of_arg_harness[@]}" -gt 0 ]];then [[ "${_one_of_arg_harness[*]}" =~ (^|[[:space:]])"$_arg_harness"($|[[:space:]]) ]] || die "harness must be one of: opencode claude gemini codex kilo";fi
                ;;

            -m|--model)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_model="$2"
                shift
                ;;
            --model=*)
                _arg_model="${_key##--model=}"
                ;;
            -m*)
                _arg_model="${_key##-m}"
                ;;

            --validation-cmd)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_validation_cmd+=("$2")
                shift
                ;;
            --validation-cmd=*)
                _arg_validation_cmd+=("${_key##--validation-cmd=}")
                ;;

            --review-model)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_review_model="$2"
                shift
                ;;
            --review-model=*)
                _arg_review_model="${_key##--review-model=}"
                ;;

            --review-output-dir)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_review_output_dir="$2"
                shift
                ;;
            --review-output-dir=*)
                _arg_review_output_dir="${_key##--review-output-dir=}"
                ;;

            --review-harness)
                test $# -lt 2 && die "Missing value for the option: '$_key'" 1
                _arg_review_harness="$2"
                if [[ "${#_one_of_arg_review_harness[@]}" -gt 0 ]];then [[ "${_one_of_arg_review_harness[*]}" =~ (^|[[:space:]])"$_arg_review_harness"($|[[:space:]]) ]] || die "review-harness must be one of: opencode claude gemini codex kilo";fi
                shift
                ;;
            --review-harness=*)
                _arg_review_harness="${_key##--review-harness=}"
                if [[ "${#_one_of_arg_review_harness[@]}" -gt 0 ]];then [[ "${_one_of_arg_review_harness[*]}" =~ (^|[[:space:]])"$_arg_review_harness"($|[[:space:]]) ]] || die "review-harness must be one of: opencode claude gemini codex kilo";fi
                ;;

            --resume)
                _arg_resume="on"
                ;;
            --no-resume)
                _arg_resume="off"
                ;;
            -n|--dry-run)
                _arg_dry_run="on"
                ;;
            --no-dry-run)
                _arg_dry_run="off"
                ;;
            --skip-commit)
                _arg_skip_commit="on"
                ;;
            --no-skip-commit)
                _arg_skip_commit="off"
                ;;
            --skip-push)
                _arg_skip_push="on"
                ;;
            --no-skip-push)
                _arg_skip_push="off"
                ;;
            -h|--help)
                print_help;
                exit 0;
                ;;
            -h*)
                print_help;
                exit 0;
                ;;
            -v|--version)
                print_version;
                exit 0;
                ;;
            -v*)
                print_version;
                exit 0;
                ;;
            --verbose)
                if [ $# -lt 2 ];then
                    _verbose_level="$((_verbose_level + 1))";
                else
                    _verbose_level="$2";
                    shift;
                fi
                ;;
            --quiet)
                if [ $# -lt 2 ];then
                    _verbose_level="$((_verbose_level - 1))";
                else
                    _verbose_level="-$2";
                    shift;
                fi
                ;;

                *)
                _last_positional="$1"
                _positionals+=("$_last_positional")
                _positionals_count=$((_positionals_count + 1))
                ;;
        esac
        shift
    done
}


handle_passed_args_count()
{
    local _required_args_string="plans-dir"
    if [ "${_positionals_count}" -gt 1 ] && [ "$_helpHasBeenPrinted" == "1" ];then
        _PRINT_HELP=yes die "FATAL ERROR: There were spurious positional arguments --- we expect at most 1 (namely: $_required_args_string), but got ${_positionals_count} (the last one was: '${_last_positional}').\n\t${_positionals[*]}" 1
    fi
    if [ "${_positionals_count}" -lt 1 ] && [ "$_helpHasBeenPrinted" == "1" ];then
        _PRINT_HELP=yes die "FATAL ERROR: Not enough positional arguments - we require at least 1 (namely: $_required_args_string), but got only ${_positionals_count}.
    ${_positionals[*]}" 1;
    fi
}


assign_positional_args()
{
    local _positional_name _shift_for=$1;
    _positional_names="_arg_plans_dir ";
    shift "$_shift_for"
    for _positional_name in ${_positional_names};do
        test $# -gt 0 || break;
        eval "if [ \"\$_one_of${_positional_name}\" != \"\" ];then [[ \"\${_one_of${_positional_name}[*]}\" =~ \"\${1}\" ]];fi" || die "${_positional_name} must be one of: $(eval "echo \"\${_one_of${_positional_name}[*]}\"")" 1;
        local _match_var="_match${_positional_name}";
        local _regex="${!_match_var}";
        if [ -n "$_regex" ]; then
            [[ "${1}" =~ $_regex ]] || die "${_positional_name} does not match pattern: $_regex"
        fi
        eval "$_positional_name=\${1}" || die "Error during argument parsing, possibly an ParseArger bug." 1;
        shift;
    done
}

print_debug()
{
    print_help
    # shellcheck disable=SC2145
    echo "DEBUG: $0 $@";

    echo -e "    plans-dir: ${_arg_plans_dir}";
    echo -e "    prds-dir: ${_arg_prds_dir}";
    echo -e "    vision: ${_arg_vision}";
    echo -e "    project-name: ${_arg_project_name}";
    echo -e "    start: ${_arg_start}";
    echo -e "    end: ${_arg_end}";
    echo -e "    harness: ${_arg_harness}";
    echo -e "    model: ${_arg_model}";
    echo -e "    validation-cmd: ${_arg_validation_cmd[*]}";
    echo -e "    review-model: ${_arg_review_model}";
    echo -e "    review-output-dir: ${_arg_review_output_dir}";
    echo -e "    review-harness: ${_arg_review_harness}";
    echo -e "    resume: ${_arg_resume}";
    echo -e "    dry-run: ${_arg_dry_run}";
    echo -e "    skip-commit: ${_arg_skip_commit}";
    echo -e "    skip-push: ${_arg_skip_push}";

}


print_version()
{
    echo "1.0.0";
}


on_interrupt() {
    die Process aborted! 130;
}


parse_commandline "$@";
handle_passed_args_count;
assign_positional_args 1 "${_positionals[@]}";
trap on_interrupt INT;




# @parseArger-parsing-end
# print_debug "$@"
# @parseArger-end

# ============================================================================
# CONFIGURATION
# ============================================================================

set -euo pipefail

PLANS_DIR="${_arg_plans_dir}"
PRDS_DIR="${_arg_prds_dir:-}"
VISION_DOC="${_arg_vision:-}"
PROJECT_NAME="${_arg_project_name}"
STATE_DIR=".task-o-matic/state"
LOG_DIR=".task-o-matic/logs"
STATE_FILE="$STATE_DIR/eric-state.json"

# Set default model for opencode if not specified
if [[ "$_arg_harness" == "opencode" && -z "$_arg_model" ]]; then
  _arg_model="zai-coding-plan/glm-4.7"
fi

# Create directories
mkdir -p "$STATE_DIR" "$LOG_DIR"

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

init_state() {
  local total_steps="$1"
  cat > "$STATE_FILE" <<EOF
{
  "project_name": "$PROJECT_NAME",
  "total_steps": $total_steps,
  "completed_steps": [],
  "current_step": 0,
  "last_run": "$(date -Iseconds)",
  "step_status": {}
}
EOF
}

update_step_status() {
  local step_num="$1"
  local status="$2"

  local temp_file
  temp_file=$(mktemp)

  jq --arg step "$step_num" --arg status "$status" --arg date "$(date -Iseconds)" '
    .step_status[$step] = $status |
    .last_run = $date |
    if $status == "completed" then
      .completed_steps += [$step | tonumber] |
      .current_step = ([$step | tonumber, .current_step] | max)
    elif $status == "failed" then
      .current_step = ($step | tonumber)
    else
      .
    end
  ' "$STATE_FILE" > "$temp_file" && mv "$temp_file" "$STATE_FILE"
}

get_last_failed_step() {
  jq -r '[.step_status | to_entries[] | select(.value == "failed") | .key | tonumber] | max // empty' "$STATE_FILE" 2>/dev/null || echo ""
}

get_step_status() {
  local step_num="$1"
  jq -r --arg step "$step_num" '.step_status[$step] // "pending"' "$STATE_FILE" 2>/dev/null || echo "pending"
}

# ============================================================================
# STEP DISCOVERY
# ============================================================================

declare -a STEP_FILES=()
declare -a STEP_NUMBERS=()
declare -A STEP_DESCRIPTIONS=()

discover_steps() {
  log "Discovering steps from $PLANS_DIR..." 0

  if [[ ! -d "$PLANS_DIR" ]]; then
    die "Plans directory not found: $PLANS_DIR" 1
  fi

  # Find all numbered markdown files
  local files
  files=$(find "$PLANS_DIR" -maxdepth 1 -type f -name '[0-9]*.md' | sort -V)

  if [[ -z "$files" ]]; then
    die "No plan files found in $PLANS_DIR (expected files like 01-*.md, 02-*.md)" 1
  fi

  local idx=0
  while IFS= read -r file; do
    local basename
    basename=$(basename "$file")

    # Extract step number from filename (e.g., 01-schema.md -> 1)
    local step_num
    step_num=$(echo "$basename" | grep -oP '^\d+' | sed 's/^0*//')

    # Extract description from frontmatter or filename
    local description
    description=$(grep -m1 '^description:' "$file" 2>/dev/null | sed 's/description:[[:space:]]*//' || echo "${basename#*-}" | sed 's/\.md$//' | tr '-' ' ')

    STEP_FILES+=("$basename")
    STEP_NUMBERS+=("$step_num")
    STEP_DESCRIPTIONS[$step_num]="$description"

    log "Found Step $step_num: $basename - $description" 2

    ((idx++)) || true
  done <<< "$files"

  log "Discovered ${#STEP_FILES[@]} steps" 1
}

get_total_steps() {
  echo "${#STEP_FILES[@]}"
}

get_step_file() {
  local step_num="$1"
  local idx=$((step_num - 1))
  echo "${STEP_FILES[$idx]}"
}

# ============================================================================
# HARNESS CONFIGURATION
# ============================================================================

build_harness_cmd() {
  local prompt_file="$1"

  HARNESS_CMD=()

  case "$_arg_harness" in
    opencode)
      HARNESS_CMD=(opencode run)
      [[ -n "$_arg_model" ]] && HARNESS_CMD+=(-m "$_arg_model")
      HARNESS_CMD+=("$(<"$prompt_file")")
      ;;
    claude)
      HARNESS_CMD=(claude -p)
      [[ -n "$_arg_model" ]] && HARNESS_CMD+=(--model "$_arg_model")
      HARNESS_CMD+=("$(<"$prompt_file")")
      ;;
    gemini)
      HARNESS_CMD=(gemini)
      [[ -n "$_arg_model" ]] && HARNESS_CMD+=(-m "$_arg_model")
      HARNESS_CMD+=(-y)
      HARNESS_CMD+=("$(<"$prompt_file")")
      ;;
    codex)
      HARNESS_CMD=(codex exec)
      [[ -n "$_arg_model" ]] && HARNESS_CMD+=(-m "$_arg_model")
      HARNESS_CMD+=(--full-auto)
      HARNESS_CMD+=("$(<"$prompt_file")")
      ;;
    kilo)
      HARNESS_CMD=(kilo run)
      [[ -n "$_arg_model" ]] && HARNESS_CMD+=(-m "$_arg_model")
      HARNESS_CMD+=(--auto)
      HARNESS_CMD+=("$(<"$prompt_file")")
      ;;
    *)
      die "Unknown harness: $_arg_harness" 1
      ;;
  esac
}

build_harness_msg_cmd() {
  local message="$1"

  HARNESS_MSG_CMD=()

  case "$_arg_harness" in
    opencode)
      HARNESS_MSG_CMD=(opencode run)
      [[ -n "$_arg_model" ]] && HARNESS_MSG_CMD+=(-m "$_arg_model")
      HARNESS_MSG_CMD+=("$message")
      ;;
    claude)
      HARNESS_MSG_CMD=(claude -p)
      [[ -n "$_arg_model" ]] && HARNESS_MSG_CMD+=(--model "$_arg_model")
      HARNESS_MSG_CMD+=("$message")
      ;;
    gemini)
      HARNESS_MSG_CMD=(gemini)
      [[ -n "$_arg_model" ]] && HARNESS_MSG_CMD+=(-m "$_arg_model")
      HARNESS_MSG_CMD+=(-y -p "$message")
      ;;
    codex)
      HARNESS_MSG_CMD=(codex exec)
      [[ -n "$_arg_model" ]] && HARNESS_MSG_CMD+=(-m "$_arg_model")
      HARNESS_MSG_CMD+=(--full-auto "$message")
      ;;
    kilo)
      HARNESS_MSG_CMD=(kilo run)
      [[ -n "$_arg_model" ]] && HARNESS_MSG_CMD+=(-m "$_arg_model")
      HARNESS_MSG_CMD+=(--auto "$message")
      ;;
    *)
      die "Unknown harness: $_arg_harness" 1
      ;;
  esac
}

run_harness_with_file() {
  local prompt_file="$1"
  local log_file="$2"

  build_harness_cmd "$prompt_file"

  log "Command: ${HARNESS_CMD[*]}" 2

  "${HARNESS_CMD[@]}" 2>&1 | tee "$log_file"
}

run_harness_with_message() {
  local message="$1"

  build_harness_msg_cmd "$message"

  log "Command: ${HARNESS_MSG_CMD[*]}" 2

  "${HARNESS_MSG_CMD[@]}"
}

# ============================================================================
# GIT OPERATIONS
# ============================================================================

commit_changes() {
  local step_num="$1"
  local step_file="$2"

  if [[ "$_arg_skip_commit" == "on" ]]; then
    log "Skipping commit (--skip-commit)" 1
    return 0
  fi

  local commit_msg="feat(orchestrate): complete step ${step_num} - ${step_file%.md}"

  log "Committing changes: $commit_msg" 0

  # Check if there are changes to commit
  if git diff --quiet && git diff --staged --quiet 2>/dev/null; then
    log "No changes to commit" 1
    return 0
  fi

  local commit_prompt="Please commit all current changes with this exact message: '${commit_msg}'. Run: git add -A && git commit -m '${commit_msg}'"

  if [[ "$_arg_dry_run" == "on" ]]; then
    build_harness_msg_cmd "$commit_prompt"
    log "[DRY-RUN] Would execute: ${HARNESS_MSG_CMD[*]}" 0
    return 0
  fi

  log "Executing commit via ${_arg_harness}..." 1
  if run_harness_with_message "$commit_prompt"; then
    log "Commit successful" 1
    return 0
  else
    log "Commit failed, falling back to direct git commit" -1
    git add -A && git commit -m "$commit_msg" || true
    return 0
  fi
}

push_to_origin() {
  if [[ "$_arg_skip_push" == "on" ]]; then
    log "Skipping push (--skip-push)" 1
    return 0
  fi

  local current_branch
  current_branch=$(git branch --show-current 2>/dev/null || echo "")

  if [[ -z "$current_branch" ]]; then
    log "Not in a git repository, skipping push" 1
    return 0
  fi

  log "Pushing branch '$current_branch' to origin..." 0

  if [[ "$_arg_dry_run" == "on" ]]; then
    log "[DRY-RUN] Would execute: git push origin $current_branch" 0
    return 0
  fi

  if git push origin "$current_branch"; then
    log "Push successful" 1
    return 0
  else
    log "Push failed" -2
    return 1
  fi
}

# ============================================================================
# PROMPT GENERATION
# ============================================================================

format_validation_commands() {
  if [[ ${#_arg_validation_cmd[@]} -eq 0 ]]; then
    echo "(none specified)"
    return
  fi

  local formatted=""
  for cmd in "${_arg_validation_cmd[@]}"; do
    formatted+="   - \`$cmd\`\n"
  done
  echo -e "$formatted"
}

generate_step_prompt() {
  local step_file="$1"
  local step_num="$2"
  local total_steps="$3"
  local description="${4:-$step_file}"

  local prd_ref=""
  if [[ -n "$PRDS_DIR" && -f "$PRDS_DIR/$step_file" ]]; then
    prd_ref="- PRD: \`${PRDS_DIR}/${step_file}\`"
  fi

  local vision_ref=""
  if [[ -n "$VISION_DOC" && -f "$VISION_DOC" ]]; then
    vision_ref="- Vision: \`${VISION_DOC}\`"
  fi

  local validation_cmds
  validation_cmds=$(format_validation_commands)

  cat <<EOF
# ${PROJECT_NAME} Implementation - Step ${step_num} of ${total_steps}
## Critical Implementation Rules
1. **FULL TYPE SAFETY** - No use of \`any\` type
2. **Use Context7** for up-to-date library documentation
3. **LSP errors are NOT optional** - Fix ALL errors
4. **Stay DRY** - Follow existing patterns
5. **Run validation commands** after changes:
${validation_cmds}
## Your Task
Execute Step ${step_num} (${description}):
### Files to Read
- Plan: \`${PLANS_DIR}/${step_file}\`
${prd_ref}
${vision_ref}
### Execution
1. Read the plan file completely
2. Implement all changes described in the plan
3. Run validation commands: ${validation_cmds}
4. Fix any issues found
**THIS IS A NON-INTERACTIVE AUTOMATED RUN. THE PLAN IS PRE-APPROVED.**
### CRITICAL RULES:
- **DO NOT ASK FOR APPROVAL** - execute ALL phases autonomously
- **DO NOT STOP** - continue until all phases complete or max retries
Begin execution NOW.
EOF
}

generate_review_prompt() {
  local review_harness="$1"
  local review_model="$2"
  local review_output_dir="$3"

  # Build list of plan files
  local plan_files_list=""
  local prd_files_list=""

  for i in "${!STEP_FILES[@]}"; do
    local step_file="${STEP_FILES[$i]}"
    local step_num="${STEP_NUMBERS[$i]}"
    plan_files_list+="- Step ${step_num} Plan: \`${PLANS_DIR}/${step_file}\`\n"

    if [[ -n "$PRDS_DIR" && -f "$PRDS_DIR/$step_file" ]]; then
      prd_files_list+="- Step ${step_num} PRD: \`${PRDS_DIR}/${step_file}\`\n"
    fi
  done

  cat <<EOF
# Final Codebase Review - ${PROJECT_NAME}
## Review Process
You are conducting a thorough review of the entire codebase against the implementation PLANS (not PRDs - the PRDs are for reference only).
### PLAN Files to Review Against:
${plan_files_list}
### PRD Files for Context:
${prd_files_list}
### Step 1: Analysis
Analyze different aspects of the implementation against the PLAN files:
- Architecture review - check if implementation matches plan architecture
- Best practices audit - check patterns and conventions
- Security review - identify security issues
- Performance analysis - check for performance problems
Save findings to \`${review_output_dir}/${review_harness}/\`
### Step 2: Executive Summary
Read all review files and create an executive summary:
- What's working well
- Critical issues found
- Recommendations for fixes
### Step 3: Fix Planning
Create fix plans for identified issues:
- Plans go to \`${review_output_dir}/plans/${review_harness}/\`
- Group related fixes together
- Prioritize critical issues first
### Step 4: Master Fix Plan
Create a master fix plan:
- Group fixes into logical phases with dependencies
- Each phase should be independently executable
- Output to \`${review_output_dir}/master-fix-plan.md\`
Begin review NOW.
EOF
}

# ============================================================================
# STEP EXECUTION
# ============================================================================

run_validation_commands() {
  if [[ ${#_arg_validation_cmd[@]} -eq 0 ]]; then
    return 0
  fi

  log "Running validation commands..." 0

  for cmd in "${_arg_validation_cmd[@]}"; do
    log "Running: $cmd" 1

    if [[ "$_arg_dry_run" == "on" ]]; then
      log "[DRY-RUN] Would execute: $cmd" 0
      continue
    fi

    if eval "$cmd"; then
      log "Validation passed: $cmd" 1
    else
      log "Validation failed: $cmd" -2
      return 1
    fi
  done

  return 0
}

run_step() {
  local step_num="$1"
  local step_file
  step_file=$(get_step_file "$step_num")
  local total_steps
  total_steps=$(get_total_steps)
  local description="${STEP_DESCRIPTIONS[$step_num]:-$step_file}"
  local timestamp
  timestamp=$(date +"%Y%m%d_%H%M%S")
  local log_file="$LOG_DIR/step_${step_num}_${_arg_harness}_${timestamp}.log"

  log "Starting Step ${step_num}/${total_steps}: ${description}" 0
  log "Plan file: ${PLANS_DIR}/${step_file}" 1
  log "Harness: ${_arg_harness}${_arg_model:+ (model: $_arg_model)}" 1
  log "Log file: ${log_file}" 1

  # Check plan file exists
  if [[ ! -f "${PLANS_DIR}/${step_file}" ]]; then
    die "Plan file not found: ${PLANS_DIR}/${step_file}" 1
  fi

  # Update state to running
  update_step_status "$step_num" "running"

  # Generate prompt
  local prompt
  prompt=$(generate_step_prompt "$step_file" "$step_num" "$total_steps" "$description")

  # Save prompt to temp file
  local prompt_file
  prompt_file=$(mktemp)
  echo "$prompt" > "$prompt_file"

  log "Launching ${_arg_harness}..." 0

  if [[ "$_arg_dry_run" == "on" ]]; then
    build_harness_cmd "$prompt_file"
    log "[DRY-RUN] Would execute: ${HARNESS_CMD[*]}" 0
    log "[DRY-RUN] Prompt saved to: $prompt_file" 1
    rm -f "$prompt_file"
    return 0
  fi

  # Run the harness
  local harness_exit_code=0
  run_harness_with_file "$prompt_file" "$log_file" || harness_exit_code=$?

  rm -f "$prompt_file"

  if [[ $harness_exit_code -eq 0 ]]; then
    log "Step ${step_num} harness completed" 1
  else
    log "Step ${step_num} harness exited with code ${harness_exit_code}" -1
    log "Check log for details: ${log_file}" -1
  fi

  # Run validation commands
  if ! run_validation_commands; then
    update_step_status "$step_num" "failed"
    die "Step ${step_num} failed validation" 1
  fi

  # Mark step as completed
  update_step_status "$step_num" "completed"

  log "Step ${step_num} completed successfully" 1
  return 0
}

# ============================================================================
# REVIEW PHASE
# ============================================================================

run_review_phase() {
  if [[ -z "$_arg_review_harness" ]]; then
    return 0
  fi

  log "Starting final review phase..." 0
  log "Review harness: $_arg_review_harness${_arg_review_model:+ (model: $_arg_review_model)}" 1
  log "Output directory: $_arg_review_output_dir" 1

  # Create output directory
  mkdir -p "$_arg_review_output_dir"

  # Generate review prompt
  local prompt
  prompt=$(generate_review_prompt "$_arg_review_harness" "$_arg_review_model" "$_arg_review_output_dir")

  # Save prompt to temp file
  local prompt_file
  prompt_file=$(mktemp)
  echo "$prompt" > "$prompt_file"

  local timestamp
  timestamp=$(date +"%Y%m%d_%H%M%S")
  local model_suffix="${_arg_review_model:+_${_arg_review_model}}"
  local log_file="$LOG_DIR/review_${_arg_review_harness}${model_suffix}_${timestamp}.log"

  log "Launching review with $_arg_review_harness${_arg_review_model:+ ($_arg_review_model)}..." 0

  if [[ "$_arg_dry_run" == "on" ]]; then
    log "[DRY-RUN] Would execute review phase" 0
    log "[DRY-RUN] Prompt saved to: $prompt_file" 1
    rm -f "$prompt_file"
    return 0
  fi

  # Build review harness command
  local review_harness_cmd=()
  case "$_arg_review_harness" in
    opencode)
      review_harness_cmd=(opencode run)
      [[ -n "$_arg_review_model" ]] && review_harness_cmd+=(-m "$_arg_review_model")
      review_harness_cmd+=("$(<"$prompt_file")")
      ;;
    claude)
      review_harness_cmd=(claude -p)
      [[ -n "$_arg_review_model" ]] && review_harness_cmd+=(--model "$_arg_review_model")
      review_harness_cmd+=("$(<"$prompt_file")")
      ;;
    gemini)
      review_harness_cmd=(gemini)
      [[ -n "$_arg_review_model" ]] && review_harness_cmd+=(-m "$_arg_review_model")
      review_harness_cmd+=(-y)
      review_harness_cmd+=("$(<"$prompt_file")")
      ;;
    codex)
      review_harness_cmd=(codex exec)
      [[ -n "$_arg_review_model" ]] && review_harness_cmd+=(-m "$_arg_review_model")
      review_harness_cmd+=(--full-auto)
      review_harness_cmd+=("$(<"$prompt_file")")
      ;;
    kilo)
      review_harness_cmd=(kilo run)
      [[ -n "$_arg_review_model" ]] && review_harness_cmd+=(-m "$_arg_review_model")
      review_harness_cmd+=(--auto)
      review_harness_cmd+=("$(<"$prompt_file")")
      ;;
    *)
      die "Unknown review harness: $_arg_review_harness" 1
      ;;
  esac

  log "Command: ${review_harness_cmd[*]}" 2

  # Run review harness
  local harness_exit_code=0
  "${review_harness_cmd[@]}" 2>&1 | tee "$log_file" || harness_exit_code=$?

  rm -f "$prompt_file"

  if [[ $harness_exit_code -eq 0 ]]; then
    log "Review phase completed successfully" 1
    log "Review outputs in: $_arg_review_output_dir/$_arg_review_harness/" 1
  else
    log "Review phase exited with code ${harness_exit_code}" -1
    log "Check log for details: ${log_file}" -1
  fi

  return 0
}

# ============================================================================
# PREREQUISITES CHECK
# ============================================================================

get_harness_bin() {
  case "$_arg_harness" in
    opencode) echo "opencode" ;;
    claude) echo "claude" ;;
    gemini) echo "gemini" ;;
    codex) echo "codex" ;;
    kilo) echo "kilo" ;;
  esac
}

verify_prerequisites() {
  log "Verifying prerequisites..." 0

  # Check harness is available
  local harness_bin
  harness_bin=$(get_harness_bin)

  if ! command -v "$harness_bin" &> /dev/null; then
    die "${_arg_harness} harness not found: $harness_bin not in PATH" 1
  fi

  # Check plans directory exists
  if [[ ! -d "$PLANS_DIR" ]]; then
    die "Plans directory not found: $PLANS_DIR" 1
  fi

  # Check plan files exist
  for step_file in "${STEP_FILES[@]}"; do
    if [[ ! -f "$PLANS_DIR/$step_file" ]]; then
      die "Plan file not found: $PLANS_DIR/$step_file" 1
    fi
  done

  # Check PRD files if PRDS_DIR specified
  if [[ -n "$PRDS_DIR" ]]; then
    if [[ ! -d "$PRDS_DIR" ]]; then
      die "PRDs directory not found: $PRDS_DIR" 1
    fi

    for step_file in "${STEP_FILES[@]}"; do
      if [[ -f "$PRDS_DIR/$step_file" ]]; then
        log "Found PRD: $PRDS_DIR/$step_file" 2
      fi
    done
  fi

  # Check vision document if specified
  if [[ -n "$VISION_DOC" && ! -f "$VISION_DOC" ]]; then
    die "Vision document not found: $VISION_DOC" 1
  fi

  log "All prerequisites verified" 1
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
  # Discover steps first
  discover_steps

  local total_steps
  total_steps=$(get_total_steps)

  local start_step="${_arg_start}"
  local end_step="${_arg_end:-$total_steps}"

  # Handle resume
  if [[ "$_arg_resume" == "on" ]]; then
    if [[ -f "$STATE_FILE" ]]; then
      local last_failed
      last_failed=$(get_last_failed_step)
      if [[ -n "$last_failed" ]]; then
        log "Resuming from failed step: $last_failed" 0
        start_step="$last_failed"
      else
        log "No failed step found, starting from step $start_step" 1
      fi
    else
      log "No state file found, initializing new state" 1
      init_state "$total_steps"
    fi
  else
    init_state "$total_steps"
  fi

  # Validate step range
  if [[ "$start_step" -lt 1 ]]; then
    die "Start step must be >= 1" 1
  fi

  if [[ "$end_step" -gt "$total_steps" ]]; then
    end_step="$total_steps"
  fi

  if [[ "$start_step" -gt "$end_step" ]]; then
    die "Start step ($start_step) cannot be greater than end step ($end_step)" 1
  fi

  # Display header
  echo ""
  echo "================================================================"
  printf "  eric - AI Orchestration v1.0\n"
  echo "================================================================"
  printf "  Project: %s\n" "${PROJECT_NAME}"
  printf "  Harness: %s\n" "${_arg_harness}${_arg_model:+ ($_arg_model)}"
  printf "  Steps: %s to %s of %s\n" "${start_step}" "${end_step}" "${total_steps}"
  printf "  Plans: %s\n" "${PLANS_DIR}"
  if [[ -n "$PRDS_DIR" ]]; then
    printf "  PRDs: %s\n" "${PRDS_DIR}"
  fi
  if [[ ${#_arg_validation_cmd[@]} -gt 0 ]]; then
    printf "  Validation: %s command(s)\n" "${#_arg_validation_cmd[@]}"
  fi
  if [[ -n "$_arg_review_harness" ]]; then
    printf "  Review: %s\n" "${_arg_review_harness}${_arg_review_model:+ ($_arg_review_model)}"
  fi
  if [[ "$_arg_dry_run" == "on" ]]; then
    echo "  Mode: DRY RUN"
  fi
  echo "================================================================"
  echo ""

  # Verify prerequisites
  verify_prerequisites

  # Execute steps
  for ((i = start_step; i <= end_step; i++)); do
    local step_file
    step_file=$(get_step_file "$i")

    echo ""
    echo "----------------------------------------------------------------"
    printf "                    STEP %d OF %d\n" "$i" "$total_steps"
    echo "----------------------------------------------------------------"
    echo ""

    # Run the step
    run_step "$i"

    # Commit and push after step completes
    commit_changes "$i" "$step_file"
    push_to_origin

    log "Step ${i} complete, committed, and pushed" 1
  done

  # Run review phase if specified
  run_review_phase

  # Mark all complete
  echo ""
  echo "================================================================"
  echo "                 ALL STEPS COMPLETE"
  echo "================================================================"
  echo ""

  if [[ -n "$_arg_review_harness" ]]; then
    log "Review outputs available in: $_arg_review_output_dir/$_arg_review_harness/" 1
  fi

  log "${PROJECT_NAME} implementation complete!" 1
}

# Run main
main
