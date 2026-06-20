parser grammar dqcParser;

options {
    tokenVocab = dqcLexer;
}

/* DQC Parser - Minimalistic grammar for recognizing DQC pragma lines
 * Format: pragma dqc.vX.split id=N
 * Namespace: dqc.v1.split uses dots as separators between namespace parts
 * Chunk ID must be > 0 (validated in wrapper code)
 * Everything else is passed through as-is
 */

// Top-level program: sequence of lines
program: line* EOF;

// A line is either a DQC pragma, other content, or just a newline
line: PRAGMA_LINE NEWLINE     # pragmaLine
    | OTHER NEWLINE           # otherLine
    | NEWLINE                 # emptyLine
    ;
