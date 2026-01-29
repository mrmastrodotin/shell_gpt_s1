#compdef sgpt

# Zsh completion for sgpt

_sgpt() {
    local -a commands
    local -a agent_commands
    local -a config_commands
    
    commands=(
        'agent:Manage agent sessions'
        'run:Execute approved commands'
        'tools:Show tool availability'
        'config:Manage configuration'
        'report:Generate reports'
    )
    
    agent_commands=(
        'start:Start new agent session'
        'status:Check session status'
        'stop:Stop agent session'
        'resume:Resume agent session'
        'list:List all sessions'
        'report:Generate session report'
    )
    
    config_commands=(
        'init:Initialize default config'
        'show:Show current config'
        'set:Set config value'
        'validate:Validate config'
    )
    
    _arguments \
        '1: :->command' \
        '2: :->subcommand' \
        '*:: :->args'
    
    case $state in
        command)
            _describe 'command' commands
            ;;
        subcommand)
            case $words[2] in
                agent)
                    _describe 'subcommand' agent_commands
                    ;;
                config)
                    _describe 'subcommand' config_commands
                    ;;
                run)
                    # Complete with execution IDs
                    local exec_ids
                    exec_ids=(${(f)"$(ls ~/.sgpt/agent_sessions/*/executions/pending/*.json 2>/dev/null | xargs -n 1 basename | sed 's/\.json$//')"})
                    _describe 'execution ID' exec_ids
                    ;;
            esac
            ;;
    esac
}

_sgpt "$@"
