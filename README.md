Rule Compression System

This project implements a rule compressor for biomarker-based donor classification rules. It identifies and compresses redundant or less informative rules while preserving key insights.

The system analyzes a set of rules that classify donors into "old" or "young" categories based on biomarker measurements. It then compresses these rules by:

1. Identifying and removing redundant rules
2. Grouping similar rules and keeping only the best performing ones
3. Ranking rules by a weighted score that balances accuracy and complexity

Compression Heuristics

The compression algorithm employs the following heuristics:

Rule Redundancy Detection
A rule is considered redundant if there exists another rule that:
- Has equal or better coverage (percentage of old donors correctly identified)
- Has equal or better precision (ratio of true positives to all positives)
- Uses fewer predicates (simpler)

Similar Rule Grouping
Rules are grouped based on the exact predicates they use, regardless of how those predicates are combined. From each group, only the rule with the highest score (coverage × precision) is kept.

Rule Scoring and Ranking
The final set of non-redundant rules is ranked using an adjusted score:
