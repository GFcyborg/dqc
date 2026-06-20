lexer grammar dqcLexer;

/* DQC Lexer - Minimalistic grammar for recognizing DQC pragma lines
 * Format: pragma dqc.vX.split id=N
 * where X is the version number and N is the split-point id (must be >= 1)
 * Namespace format: dqc.v1.split uses dots as separators
 */

// Whitespace fragment (horizontal whitespace only)
fragment WS: [ \t];

// Match pragma line - entire pragma on one token
// Whitespace is required after 'pragma' and 'split', optional elsewhere
// ID must be >= 1 (matches [1-9][0-9]*)
PRAGMA_LINE: 'pragma' WS+ 'dqc' '.' 'v' [0-9]+ '.' 'split' WS+ 'id' WS* '=' WS* [1-9][0-9]* WS* ;

// Newline
NEWLINE: '\r'? '\n';

// Any other line content (must match at least one character to avoid empty string warning)
OTHER: ~[\r\n]+;
