# Polyglot fixture — to_i on a value that could be nil.
# ENV['MISSING'] returns nil when unset; .to_i on nil raises NoMethodError.
# Parses clean; rubocop Lint/NilChecks / Lint/SafeNavigationChain would flag line 6.

def parse_port
  ENV['MISSING'].to_i
end

def main
  puts parse_port
end

main
