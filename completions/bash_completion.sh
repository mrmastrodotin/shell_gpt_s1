# Bash completion for sgpt
# Source this file or add to ~/.bashrc

_sgpt_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Main commands
    local commands="agent run tools config report"
    
    # Agent subcommands
    local agent_commands="start status stop resume list report"
    
    # Config subcommands
    local config_commands="init show set validate"
    
    # First level completion
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    # Second level completion
    case "${COMP_WORDS[1]}" in
        agent)
            if [ $COMP_CWORD -eq 2 ]; then
                COMPREPLY=( $(compgen -W "${agent_commands}" -- ${cur}) )
            fi
            ;;
        config)
            if [ $COMP_CWORD -eq 2 ]; then
                COMPREPLY=( $(compgen -W "${config_commands}" -- ${cur}) )
            fi
            ;;
        run)
            # Complete with execution IDs or commands
            if [ $COMP_CWORD -eq 2 ]; then
                local exec_ids=$(ls ~/.sgpt/agent_sessions/*/executions/pending/*.json 2>/dev/null | xargs -n 1 basename | sed 's/\.json$//')
                COMPREPLY=( $(compgen -W "${exec_ids}" -- ${cur}) )
            fi
            ;;
    esac
}

complete -F _sgpt_completion sgpt
