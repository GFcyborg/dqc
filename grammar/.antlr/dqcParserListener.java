// Generated from /home/gf/Documents/SPDM801_thesis/dqc/grammar/dqcParser.g4 by ANTLR 4.13.1
import org.antlr.v4.runtime.tree.ParseTreeListener;

/**
 * This interface defines a complete listener for a parse tree produced by
 * {@link dqcParser}.
 */
public interface dqcParserListener extends ParseTreeListener {
	/**
	 * Enter a parse tree produced by {@link dqcParser#program}.
	 * @param ctx the parse tree
	 */
	void enterProgram(dqcParser.ProgramContext ctx);
	/**
	 * Exit a parse tree produced by {@link dqcParser#program}.
	 * @param ctx the parse tree
	 */
	void exitProgram(dqcParser.ProgramContext ctx);
	/**
	 * Enter a parse tree produced by the {@code pragmaLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void enterPragmaLine(dqcParser.PragmaLineContext ctx);
	/**
	 * Exit a parse tree produced by the {@code pragmaLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void exitPragmaLine(dqcParser.PragmaLineContext ctx);
	/**
	 * Enter a parse tree produced by the {@code otherLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void enterOtherLine(dqcParser.OtherLineContext ctx);
	/**
	 * Exit a parse tree produced by the {@code otherLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void exitOtherLine(dqcParser.OtherLineContext ctx);
	/**
	 * Enter a parse tree produced by the {@code emptyLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void enterEmptyLine(dqcParser.EmptyLineContext ctx);
	/**
	 * Exit a parse tree produced by the {@code emptyLine}
	 * labeled alternative in {@link dqcParser#line}.
	 * @param ctx the parse tree
	 */
	void exitEmptyLine(dqcParser.EmptyLineContext ctx);
}