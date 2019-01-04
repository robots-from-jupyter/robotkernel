// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under a MIT license: http://codemirror.net/LICENSE

// brackets-robotframework, copyright (c) by Bryan Oakley
// Distributed under a MIT license

CodeMirror.defineMode("robotframework", function() {
  function canonicalTableName(name) {
    // This returns the canonical (internal) name for a table,
    // which will be one of "settings", "test_cases",
    // "keywords", or "variables"
    //
    // This function will return null if name isn't one of the
    // strings supported by robot
    name = name.trim().toLowerCase();
    if (name.match("settings?|metadata")) {
      return "settings";
    }
    if (name.match("test ?cases?")) {
      return "test_cases";
    }
    if (name.match("tasks")) {
      return "test_cases";
    }
    if (name.match("(user )?keywords?")) {
      return "keywords";
    }
    if (name.match("variables?")) {
      return "variables";
    }
    return null;
  }

  function isHeading(stream, state) {
    // this matches things like "*** Test Cases ***", "*** Keywors ***", etc
    // It tries to strictly follow the robot specification, which implies you
    // can have more than one asterisk, and trailing asterisks are optional,
    // and the table names must be one of the recognized table names
    if (stream.sol()) {
      var match = stream.match(
          /^\s*\*+\s*(settings?|metadata|variables?|test ?cases?|tasks|(user )?keywords?)[ *]*$/i
      );
      if (match !== null) {
        state.table_name = canonicalTableName(match[1]);
        state.tc_or_kw_name = null;
        stream.skipToEnd();
        return true;
      }
    }
    return false;
  }

  function isSpecial(stream, state) {
    var cell = stream.current().trim();
    // this isn't 100% precise, but it's good enough for now.
    if ([":FOR", "IN", "IN RANGE",
         "WITH NAME", "AND", "ELSE"].indexOf(cell) >= 0) {
      return true;
    }
  }

  function isContinuation(stream, state) {
    // Return true if the stream is currently in a
    // continuation cell. This will catch random data
    // that is not the first non-empty cell on a line,
    // but that's such a rare thing that it's not a
    // big deal.
    return stream.current().trim() === "...";
  }

  function isSetting(stream, state) {
    // Return true if the stream is in a settings table and the
    // token is a valid setting
    if (state.isSettingsTable() && state.column === 0) {
      var s = stream
          .current()
          .trim()
          .toLowerCase();
      if (
          s.match(
              "^(library|resource|variables|documentation|metadata|" +
              "suite setup|suite teardown|suite precondition|" +
              "suite postcondition|force tags|default tags|test setup|" +
              "test teardown|test precondition|test postcondition|" +
              "test template|test timeout|" +
              "task setup|" +
              "task teardown|task precondition|task postcondition|" +
              "task template|task timeout)$"
          )
      ) {
        return true;
      }
    }
    return false;
  }

  function isLocalSetting(stream, state) {
    var s = stream
        .current()
        .trim()
        .toLowerCase();
    if (state.isTestCasesTable()) {
      if (
          s.match(
              "\\[(documentation|tags|setup|teardown|precondition|postcondition|template|timeout)\\]"
          )
      ) {
        return true;
      }
    } else if (state.isKeywordsTable()) {
      if (s.match("\\[(documentation|arguments|return|timeout)\\]")) {
        return true;
      }
    }
    return false;
  }

  function isName(stream, state) {
    // Return true if this is the first column in a test case or keyword table
    if (
        state.column === 0 &&
        (state.isTestCasesTable() || state.isKeywordsTable())
    ) {
      state.tc_or_kw_name = stream.current();
      return true;
    }
    return false;
  }

  function isKeyword(stream, state) {
    // Return true if this is the second column in a test case or keyword table
    if (
        state.column === 1 &&
        (state.isTestCasesTable() || state.isKeywordsTable())
    ) {
      state.tc_or_kw_name = stream.current();
      return true;
    } else if (
        state.column === 2 &&
        (state.isTestCasesTable() || state.isKeywordsTable()) &&
        !state.tc_or_kw_name
    ) {
      state.tc_or_kw_name = stream.current();
      return true;
    }
    return false;
  }

  function isVariable(stream, state) {
    // Return true if trimmed value looks like a variable
    var s = stream
        .current()
        .trim()
        .toLowerCase();
    if (s.match("^[$@&%]{")) {
      if (state.column === 1) {
        state.tc_or_kw_name = null;
      }
      return true;
    }
    return false;
  }

  function isOperator(stream, state) {
    // Return true if trimmed value looks like a variable
    var s = stream
        .current()
        .trim()
        .toLowerCase();
    if (s.match("^[=:]$")) {
      return true;
    }
    return false;
  }

  function isSubheading(stream, state) {
    // Return true if a cell begins with two or more colons
    // (eg: ":: Log in") Admittedly, this is a non-standard
    // feature, but it should be pretty harmless (or useful!)
    // for others. My team defines a keyword named ":: {$text}"
    // which we use to organize our code in a long test case
    // or keyword.
    if (stream.match(/^\s*:::? \S.*$/)) {
      return true;
    }
    return false;
  }

  function isComment(stream, state) {
    // Return true if a cell begins with a hash (and optional leading whitesp
    if (stream.match(/^\s*#/)) {
      return true;
    }
    return false;
  }

  function isSeparator(stream) {
    // Return true if the stream is currently in a separator
    // (read: tab, or two or more whitespace characters
    var match = stream.match(/(\t|\s{2,})/);
    return match;
  }

  function eatCellContents(stream, state) {
    // gobble up characters until the end of the line or we find a separator

    var ch;
    var first = true;
    while ((ch = stream.next()) != null) {
      if (ch === "\\") {
        // escaped character; gobble up the following character
        stream.next();
      } else if (ch === "'" || ch === "\"") {
        break;
      } else if (ch === "}" || ch === "]") {
        break;
      } else if (ch === "[") {
        if (!first) {
          stream.backUp(1);
        }
        break;
      } else if (
          (ch === "=" || ch === ":") &&
          !stream.current().match(/https?/)
      ) {
        if (!first) {
          stream.backUp(1);
        }
        break;
      } else if (ch === "\t") {
        stream.backUp(1);
        break;
      } else if (ch === " ") {
        if (stream.match(/\s/, false)) {
          stream.backUp(1);
          break;
        }
      }
      first = false;
    }
    return stream.current().length > 0;
  }

  return {
    startState: function() {
      return {
        table_name: null,
        tc_or_kw_name: null,
        column: -1,
        separator: "pipes", // maybe we should get this from preferences?
        isSettingsTable: function() {
          return this.table_name === "settings";
        },
        isVariablesTable: function() {
          return this.table_name === "variables";
        },
        isTestCasesTable: function() {
          return this.table_name === "test_cases";
        },
        isKeywordsTable: function() {
          return this.table_name === "keywords";
        },
        pipeSeparated: function() {
          return this.separator == "pipes";
        },
        spaceSeparated: function() {
          return this.separator == "spaces";
        },
        tabSeparated: function() {
          return this.separator == "tabs";
        }
      };
    },

    token: function(stream, state) {
      // determine separator mode for this line -- pipes or spaces
      if (stream.sol()) {
        state.column = 0;
        state.separator = "spaces";
      }

      // comments
      if (isComment(stream, state)) {
        stream.skipToEnd();
        return "comment";
      }

      // table headings (eg: *** Test Cases ***)
      if (isHeading(stream, state)) {
        return "header";
      }

      // subheadings
      // A subheading is a nonstandard thing my team uses. See
      // the definition of isSubheading for more information...
      if (isSubheading(stream, state)) {
        // It makes sense to use "header" here, but we're already
        // using "header", and it has behavior assocated with it.
        //
        // "def" isn't pendantically correct, but this extension
        // doesn't use "def" for anything else, so we might as well
        // use it for this. Pretend "def" means "defines a section"
        return "def";
      }

      // N.B. Don't ever use "cell-separator" for anything
      // but cell separators. We use this for parsing tokens
      // in other places in the code.
      if (isSeparator(stream, state)) {
        state.column += 1;
        // this is a custom class (cm-cell-separator)
        // defined in main.js
        return "cell-separator";
      }

      var c;
      if ((c = eatCellContents(stream, state))) {
        // a table cell; it may be one of several flavors
        if (isContinuation(stream, state)) {
          return "meta";
        }
        if (isLocalSetting(stream, state)) {
          return "builtin";
        }
        if (isSetting(stream, state)) {
          return "attribute";
        }
        if (isName(stream, state)) {
          return "keyword";
        }
        if (isOperator(stream, state)) {
          return "operator";
        }
        if (isVariable(stream, state)) {
          return "string";
        }
        if (isKeyword(stream, state)) {
          return "tag";
        }
      }

      // special constructs, like :FOR
      if (isSpecial(stream, state)) {
        return "builtin";
      }

      return null;
    }
  };
});
