Value DOMAIN_NAME ([\w+.]+)

Start
  ^\s+Domain\s+Source\s+Interface\s+Preference -> Domains
  ^\s+Source\s+Interface\s+Preference\s+Domain -> Domains

Domains
  ^${DOMAIN_NAME} -> Record End
