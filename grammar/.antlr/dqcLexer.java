// Generated from /home/gf/Documents/SPDM801_thesis/dqc/grammar/dqcLexer.g4 by ANTLR 4.13.1
import org.antlr.v4.runtime.Lexer;
import org.antlr.v4.runtime.CharStream;
import org.antlr.v4.runtime.Token;
import org.antlr.v4.runtime.TokenStream;
import org.antlr.v4.runtime.*;
import org.antlr.v4.runtime.atn.*;
import org.antlr.v4.runtime.dfa.DFA;
import org.antlr.v4.runtime.misc.*;

@SuppressWarnings({"all", "warnings", "unchecked", "unused", "cast", "CheckReturnValue", "this-escape"})
public class dqcLexer extends Lexer {
	static { RuntimeMetaData.checkVersion("4.13.1", RuntimeMetaData.VERSION); }

	protected static final DFA[] _decisionToDFA;
	protected static final PredictionContextCache _sharedContextCache =
		new PredictionContextCache();
	public static final int
		PRAGMA_LINE=1, NEWLINE=2, OTHER=3;
	public static String[] channelNames = {
		"DEFAULT_TOKEN_CHANNEL", "HIDDEN"
	};

	public static String[] modeNames = {
		"DEFAULT_MODE"
	};

	private static String[] makeRuleNames() {
		return new String[] {
			"WS", "PRAGMA_LINE", "NEWLINE", "OTHER"
		};
	}
	public static final String[] ruleNames = makeRuleNames();

	private static String[] makeLiteralNames() {
		return new String[] {
		};
	}
	private static final String[] _LITERAL_NAMES = makeLiteralNames();
	private static String[] makeSymbolicNames() {
		return new String[] {
			null, "PRAGMA_LINE", "NEWLINE", "OTHER"
		};
	}
	private static final String[] _SYMBOLIC_NAMES = makeSymbolicNames();
	public static final Vocabulary VOCABULARY = new VocabularyImpl(_LITERAL_NAMES, _SYMBOLIC_NAMES);

	/**
	 * @deprecated Use {@link #VOCABULARY} instead.
	 */
	@Deprecated
	public static final String[] tokenNames;
	static {
		tokenNames = new String[_SYMBOLIC_NAMES.length];
		for (int i = 0; i < tokenNames.length; i++) {
			tokenNames[i] = VOCABULARY.getLiteralName(i);
			if (tokenNames[i] == null) {
				tokenNames[i] = VOCABULARY.getSymbolicName(i);
			}

			if (tokenNames[i] == null) {
				tokenNames[i] = "<INVALID>";
			}
		}
	}

	@Override
	@Deprecated
	public String[] getTokenNames() {
		return tokenNames;
	}

	@Override

	public Vocabulary getVocabulary() {
		return VOCABULARY;
	}


	public dqcLexer(CharStream input) {
		super(input);
		_interp = new LexerATNSimulator(this,_ATN,_decisionToDFA,_sharedContextCache);
	}

	@Override
	public String getGrammarFileName() { return "dqcLexer.g4"; }

	@Override
	public String[] getRuleNames() { return ruleNames; }

	@Override
	public String getSerializedATN() { return _serializedATN; }

	@Override
	public String[] getChannelNames() { return channelNames; }

	@Override
	public String[] getModeNames() { return modeNames; }

	@Override
	public ATN getATN() { return _ATN; }

	public static final String _serializedATN =
		"\u0004\u0000\u0003U\u0006\uffff\uffff\u0002\u0000\u0007\u0000\u0002\u0001"+
		"\u0007\u0001\u0002\u0002\u0007\u0002\u0002\u0003\u0007\u0003\u0001\u0000"+
		"\u0001\u0000\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001"+
		"\u0001\u0001\u0001\u0001\u0001\u0001\u0004\u0001\u0014\b\u0001\u000b\u0001"+
		"\f\u0001\u0015\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001"+
		"\u0001\u0001\u0001\u0001\u0004\u0001\u001f\b\u0001\u000b\u0001\f\u0001"+
		" \u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001"+
		"\u0001\u0001\u0001\u0001\u0004\u0001+\b\u0001\u000b\u0001\f\u0001,\u0001"+
		"\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0005\u00013\b\u0001\n\u0001"+
		"\f\u00016\t\u0001\u0001\u0001\u0001\u0001\u0005\u0001:\b\u0001\n\u0001"+
		"\f\u0001=\t\u0001\u0001\u0001\u0001\u0001\u0005\u0001A\b\u0001\n\u0001"+
		"\f\u0001D\t\u0001\u0001\u0001\u0005\u0001G\b\u0001\n\u0001\f\u0001J\t"+
		"\u0001\u0001\u0002\u0003\u0002M\b\u0002\u0001\u0002\u0001\u0002\u0001"+
		"\u0003\u0004\u0003R\b\u0003\u000b\u0003\f\u0003S\u0000\u0000\u0004\u0001"+
		"\u0000\u0003\u0001\u0005\u0002\u0007\u0003\u0001\u0000\u0004\u0002\u0000"+
		"\t\t  \u0001\u000009\u0001\u000019\u0002\u0000\n\n\r\r\\\u0000\u0003\u0001"+
		"\u0000\u0000\u0000\u0000\u0005\u0001\u0000\u0000\u0000\u0000\u0007\u0001"+
		"\u0000\u0000\u0000\u0001\t\u0001\u0000\u0000\u0000\u0003\u000b\u0001\u0000"+
		"\u0000\u0000\u0005L\u0001\u0000\u0000\u0000\u0007Q\u0001\u0000\u0000\u0000"+
		"\t\n\u0007\u0000\u0000\u0000\n\u0002\u0001\u0000\u0000\u0000\u000b\f\u0005"+
		"p\u0000\u0000\f\r\u0005r\u0000\u0000\r\u000e\u0005a\u0000\u0000\u000e"+
		"\u000f\u0005g\u0000\u0000\u000f\u0010\u0005m\u0000\u0000\u0010\u0011\u0005"+
		"a\u0000\u0000\u0011\u0013\u0001\u0000\u0000\u0000\u0012\u0014\u0003\u0001"+
		"\u0000\u0000\u0013\u0012\u0001\u0000\u0000\u0000\u0014\u0015\u0001\u0000"+
		"\u0000\u0000\u0015\u0013\u0001\u0000\u0000\u0000\u0015\u0016\u0001\u0000"+
		"\u0000\u0000\u0016\u0017\u0001\u0000\u0000\u0000\u0017\u0018\u0005d\u0000"+
		"\u0000\u0018\u0019\u0005q\u0000\u0000\u0019\u001a\u0005c\u0000\u0000\u001a"+
		"\u001b\u0001\u0000\u0000\u0000\u001b\u001c\u0005.\u0000\u0000\u001c\u001e"+
		"\u0005v\u0000\u0000\u001d\u001f\u0007\u0001\u0000\u0000\u001e\u001d\u0001"+
		"\u0000\u0000\u0000\u001f \u0001\u0000\u0000\u0000 \u001e\u0001\u0000\u0000"+
		"\u0000 !\u0001\u0000\u0000\u0000!\"\u0001\u0000\u0000\u0000\"#\u0005."+
		"\u0000\u0000#$\u0005s\u0000\u0000$%\u0005p\u0000\u0000%&\u0005l\u0000"+
		"\u0000&\'\u0005i\u0000\u0000\'(\u0005t\u0000\u0000(*\u0001\u0000\u0000"+
		"\u0000)+\u0003\u0001\u0000\u0000*)\u0001\u0000\u0000\u0000+,\u0001\u0000"+
		"\u0000\u0000,*\u0001\u0000\u0000\u0000,-\u0001\u0000\u0000\u0000-.\u0001"+
		"\u0000\u0000\u0000./\u0005i\u0000\u0000/0\u0005d\u0000\u000004\u0001\u0000"+
		"\u0000\u000013\u0003\u0001\u0000\u000021\u0001\u0000\u0000\u000036\u0001"+
		"\u0000\u0000\u000042\u0001\u0000\u0000\u000045\u0001\u0000\u0000\u0000"+
		"57\u0001\u0000\u0000\u000064\u0001\u0000\u0000\u00007;\u0005=\u0000\u0000"+
		"8:\u0003\u0001\u0000\u000098\u0001\u0000\u0000\u0000:=\u0001\u0000\u0000"+
		"\u0000;9\u0001\u0000\u0000\u0000;<\u0001\u0000\u0000\u0000<>\u0001\u0000"+
		"\u0000\u0000=;\u0001\u0000\u0000\u0000>B\u0007\u0002\u0000\u0000?A\u0007"+
		"\u0001\u0000\u0000@?\u0001\u0000\u0000\u0000AD\u0001\u0000\u0000\u0000"+
		"B@\u0001\u0000\u0000\u0000BC\u0001\u0000\u0000\u0000CH\u0001\u0000\u0000"+
		"\u0000DB\u0001\u0000\u0000\u0000EG\u0003\u0001\u0000\u0000FE\u0001\u0000"+
		"\u0000\u0000GJ\u0001\u0000\u0000\u0000HF\u0001\u0000\u0000\u0000HI\u0001"+
		"\u0000\u0000\u0000I\u0004\u0001\u0000\u0000\u0000JH\u0001\u0000\u0000"+
		"\u0000KM\u0005\r\u0000\u0000LK\u0001\u0000\u0000\u0000LM\u0001\u0000\u0000"+
		"\u0000MN\u0001\u0000\u0000\u0000NO\u0005\n\u0000\u0000O\u0006\u0001\u0000"+
		"\u0000\u0000PR\b\u0003\u0000\u0000QP\u0001\u0000\u0000\u0000RS\u0001\u0000"+
		"\u0000\u0000SQ\u0001\u0000\u0000\u0000ST\u0001\u0000\u0000\u0000T\b\u0001"+
		"\u0000\u0000\u0000\n\u0000\u0015 ,4;BHLS\u0000";
	public static final ATN _ATN =
		new ATNDeserializer().deserialize(_serializedATN.toCharArray());
	static {
		_decisionToDFA = new DFA[_ATN.getNumberOfDecisions()];
		for (int i = 0; i < _ATN.getNumberOfDecisions(); i++) {
			_decisionToDFA[i] = new DFA(_ATN.getDecisionState(i), i);
		}
	}
}