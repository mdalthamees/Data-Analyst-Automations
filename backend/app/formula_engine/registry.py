"""
Excel Function Registry:
Documents support status, category, syntax, descriptions, and test specifications
for Excel-compatible functions in DataPilot AI.
"""

from typing import Dict, Any, List

FUNCTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Mathematical & Aggregation
    "SUM": {
        "family": "Mathematical",
        "syntax": "SUM(number1, [number2], ...)",
        "description": "Adds all numbers in a range of cells or series.",
        "status": "fully_supported"
    },
    "SUMIF": {
        "family": "Mathematical",
        "syntax": "SUMIF(range, criteria, [sum_range])",
        "description": "Adds the cells specified by a given condition or criteria.",
        "status": "fully_supported"
    },
    "SUMIFS": {
        "family": "Mathematical",
        "syntax": "SUMIFS(sum_range, criteria_range1, criteria1, ...)",
        "description": "Adds cells that meet multiple criteria.",
        "status": "fully_supported"
    },
    "AVERAGE": {
        "family": "Mathematical",
        "syntax": "AVERAGE(number1, [number2], ...)",
        "description": "Returns the average (arithmetic mean) of its arguments.",
        "status": "fully_supported"
    },
    "AVERAGEIF": {
        "family": "Mathematical",
        "syntax": "AVERAGEIF(range, criteria, [average_range])",
        "description": "Returns the average of cells that meet a given condition.",
        "status": "fully_supported"
    },
    "AVERAGEIFS": {
        "family": "Mathematical",
        "syntax": "AVERAGEIFS(average_range, criteria_range1, criteria1, ...)",
        "description": "Returns the average of cells meeting multiple criteria.",
        "status": "fully_supported"
    },
    "MIN": {
        "family": "Mathematical",
        "syntax": "MIN(number1, [number2], ...)",
        "description": "Returns the smallest number in a set of values.",
        "status": "fully_supported"
    },
    "MAX": {
        "family": "Mathematical",
        "syntax": "MAX(number1, [number2], ...)",
        "description": "Returns the largest number in a set of values.",
        "status": "fully_supported"
    },
    "COUNT": {
        "family": "Mathematical",
        "syntax": "COUNT(value1, [value2], ...)",
        "description": "Counts how many numbers are in the list of arguments.",
        "status": "fully_supported"
    },
    "COUNTA": {
        "family": "Mathematical",
        "syntax": "COUNTA(value1, [value2], ...)",
        "description": "Counts the number of cells that are not empty.",
        "status": "fully_supported"
    },
    "COUNTBLANK": {
        "family": "Mathematical",
        "syntax": "COUNTBLANK(range)",
        "description": "Counts empty cells in a specified range of cells.",
        "status": "fully_supported"
    },
    "COUNTIF": {
        "family": "Mathematical",
        "syntax": "COUNTIF(range, criteria)",
        "description": "Counts the number of cells within a range that meet the given criteria.",
        "status": "fully_supported"
    },
    "COUNTIFS": {
        "family": "Mathematical",
        "syntax": "COUNTIFS(criteria_range1, criteria1, ...)",
        "description": "Counts the number of cells that meet multiple criteria.",
        "status": "fully_supported"
    },
    "PRODUCT": {
        "family": "Mathematical",
        "syntax": "PRODUCT(number1, [number2], ...)",
        "description": "Multiplies all the numbers given as arguments.",
        "status": "fully_supported"
    },
    "ABS": {
        "family": "Mathematical",
        "syntax": "ABS(number)",
        "description": "Returns the absolute value of a number.",
        "status": "fully_supported"
    },
    "ROUND": {
        "family": "Mathematical",
        "syntax": "ROUND(number, num_digits)",
        "description": "Rounds a number to a specified number of digits.",
        "status": "fully_supported"
    },
    "ROUNDUP": {
        "family": "Mathematical",
        "syntax": "ROUNDUP(number, num_digits)",
        "description": "Rounds a number up, away from 0 (zero).",
        "status": "fully_supported"
    },
    "ROUNDDOWN": {
        "family": "Mathematical",
        "syntax": "ROUNDDOWN(number, num_digits)",
        "description": "Rounds a number down, toward 0 (zero).",
        "status": "fully_supported"
    },
    "INT": {
        "family": "Mathematical",
        "syntax": "INT(number)",
        "description": "Rounds a number down to the nearest integer.",
        "status": "fully_supported"
    },
    "MOD": {
        "family": "Mathematical",
        "syntax": "MOD(number, divisor)",
        "description": "Returns the remainder after number is divided by divisor.",
        "status": "fully_supported"
    },
    "POWER": {
        "family": "Mathematical",
        "syntax": "POWER(number, power)",
        "description": "Returns the result of a number raised to a power.",
        "status": "fully_supported"
    },
    "SQRT": {
        "family": "Mathematical",
        "syntax": "SQRT(number)",
        "description": "Returns a positive square root.",
        "status": "fully_supported"
    },
    "SUBTOTAL": {
        "family": "Mathematical",
        "syntax": "SUBTOTAL(function_num, ref1, ...)",
        "description": "Returns a subtotal in a list or database.",
        "status": "fully_supported"
    },
    "AGGREGATE": {
        "family": "Mathematical",
        "syntax": "AGGREGATE(function_num, options, array, ...)",
        "description": "Returns an aggregate in a list or database with error-ignoring options.",
        "status": "fully_supported"
    },
    "SUMPRODUCT": {
        "family": "Mathematical",
        "syntax": "SUMPRODUCT(array1, [array2], ...)",
        "description": "Multiplies corresponding components in given arrays, and returns the sum of products.",
        "status": "fully_supported"
    },

    # Logical
    "IF": {
        "family": "Logical",
        "syntax": "IF(logical_test, [value_if_true], [value_if_false])",
        "description": "Specifies a logical test to perform.",
        "status": "fully_supported"
    },
    "IFS": {
        "family": "Logical",
        "syntax": "IFS(logical_test1, value_if_true1, ...)",
        "description": "Checks whether one or more conditions are met and returns a value corresponding to the first TRUE condition.",
        "status": "fully_supported"
    },
    "AND": {
        "family": "Logical",
        "syntax": "AND(logical1, [logical2], ...)",
        "description": "Returns TRUE if all of its arguments are TRUE.",
        "status": "fully_supported"
    },
    "OR": {
        "family": "Logical",
        "syntax": "OR(logical1, [logical2], ...)",
        "description": "Returns TRUE if any argument is TRUE.",
        "status": "fully_supported"
    },
    "NOT": {
        "family": "Logical",
        "syntax": "NOT(logical)",
        "description": "Reverses the logic of its argument.",
        "status": "fully_supported"
    },
    "IFERROR": {
        "family": "Logical",
        "syntax": "IFERROR(value, value_if_error)",
        "description": "Returns a value you specify if a formula evaluates to an error; otherwise, returns the result of the formula.",
        "status": "fully_supported"
    },
    "IFNA": {
        "family": "Logical",
        "syntax": "IFNA(value, value_if_na)",
        "description": "Returns the value you specify if the expression resolves to #N/A, otherwise returns the result.",
        "status": "fully_supported"
    },
    "SWITCH": {
        "family": "Logical",
        "syntax": "SWITCH(expression, value1, result1, ..., [default])",
        "description": "Evaluates an expression against a list of values and returns the result corresponding to the first matching value.",
        "status": "fully_supported"
    },
    "TRUE": {
        "family": "Logical",
        "syntax": "TRUE()",
        "description": "Returns the logical value TRUE.",
        "status": "fully_supported"
    },
    "FALSE": {
        "family": "Logical",
        "syntax": "FALSE()",
        "description": "Returns the logical value FALSE.",
        "status": "fully_supported"
    },

    # Lookup & Reference
    "XLOOKUP": {
        "family": "Lookup & Reference",
        "syntax": "XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])",
        "description": "Searches a range or array, and returns an item corresponding to the first match it finds.",
        "status": "fully_supported"
    },
    "VLOOKUP": {
        "family": "Lookup & Reference",
        "syntax": "VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])",
        "description": "Looks for a value in the leftmost column of a table, and returns a value in the same row from a specified column.",
        "status": "fully_supported"
    },
    "HLOOKUP": {
        "family": "Lookup & Reference",
        "syntax": "HLOOKUP(lookup_value, table_array, row_index_num, [range_lookup])",
        "description": "Looks for a value in the top row of a table or an array of values, and returns a value in the same column from a specified row.",
        "status": "fully_supported"
    },
    "INDEX": {
        "family": "Lookup & Reference",
        "syntax": "INDEX(array, row_num, [column_num])",
        "description": "Returns the value of an element in a table or an array, selected by row and column number indexes.",
        "status": "fully_supported"
    },
    "MATCH": {
        "family": "Lookup & Reference",
        "syntax": "MATCH(lookup_value, lookup_array, [match_type])",
        "description": "Returns the relative position of an item in an array that matches a specified value in a specified order.",
        "status": "fully_supported"
    },
    "XMATCH": {
        "family": "Lookup & Reference",
        "syntax": "XMATCH(lookup_value, lookup_array, [match_mode], [search_mode])",
        "description": "Returns the relative position of an item in an array or range of cells.",
        "status": "fully_supported"
    },
    "CHOOSE": {
        "family": "Lookup & Reference",
        "syntax": "CHOOSE(index_num, value1, [value2], ...)",
        "description": "Chooses a value from a list of values.",
        "status": "fully_supported"
    },
    "FILTER": {
        "family": "Lookup & Reference",
        "syntax": "FILTER(array, include, [if_empty])",
        "description": "Filters a range of data based on criteria you define.",
        "status": "fully_supported"
    },
    "SORT": {
        "family": "Lookup & Reference",
        "syntax": "SORT(array, [sort_index], [sort_order], [by_col])",
        "description": "Sorts the contents of a range or array.",
        "status": "fully_supported"
    },
    "SORTBY": {
        "family": "Lookup & Reference",
        "syntax": "SORTBY(array, by_array1, [sort_order1], ...)",
        "description": "Sorts the contents of a range or array based on the values in a corresponding range or array.",
        "status": "fully_supported"
    },
    "UNIQUE": {
        "family": "Lookup & Reference",
        "syntax": "UNIQUE(array, [by_col], [exactly_once])",
        "description": "Returns a list of unique values in a list or range.",
        "status": "fully_supported"
    },
    "OFFSET": {
        "family": "Lookup & Reference",
        "syntax": "OFFSET(reference, rows, cols, [height], [width])",
        "description": "Returns a reference to a range that is a specified number of rows and columns from a cell or range.",
        "status": "partially_supported"
    },

    # Text
    "LEFT": {
        "family": "Text",
        "syntax": "LEFT(text, [num_chars])",
        "description": "Returns the first character or characters in a text string, based on the number of characters you specify.",
        "status": "fully_supported"
    },
    "RIGHT": {
        "family": "Text",
        "syntax": "RIGHT(text, [num_chars])",
        "description": "Returns the last character or characters in a text string, based on the number of characters you specify.",
        "status": "fully_supported"
    },
    "MID": {
        "family": "Text",
        "syntax": "MID(text, start_num, num_chars)",
        "description": "Returns a specific number of characters from a text string, starting at the position you specify.",
        "status": "fully_supported"
    },
    "LEN": {
        "family": "Text",
        "syntax": "LEN(text)",
        "description": "Returns the number of characters in a text string.",
        "status": "fully_supported"
    },
    "TRIM": {
        "family": "Text",
        "syntax": "TRIM(text)",
        "description": "Removes all spaces from text except for single spaces between words.",
        "status": "fully_supported"
    },
    "CLEAN": {
        "family": "Text",
        "syntax": "CLEAN(text)",
        "description": "Removes all nonprintable characters from text.",
        "status": "fully_supported"
    },
    "UPPER": {
        "family": "Text",
        "syntax": "UPPER(text)",
        "description": "Converts text to uppercase.",
        "status": "fully_supported"
    },
    "LOWER": {
        "family": "Text",
        "syntax": "LOWER(text)",
        "description": "Converts text to lowercase.",
        "status": "fully_supported"
    },
    "PROPER": {
        "family": "Text",
        "syntax": "PROPER(text)",
        "description": "Capitalizes the first letter in each word of a text value.",
        "status": "fully_supported"
    },
    "CONCAT": {
        "family": "Text",
        "syntax": "CONCAT(text1, [text2], ...)",
        "description": "Combines the text from multiple ranges and/or strings.",
        "status": "fully_supported"
    },
    "CONCATENATE": {
        "family": "Text",
        "syntax": "CONCATENATE(text1, [text2], ...)",
        "description": "Joins several text items into one text item.",
        "status": "fully_supported"
    },
    "TEXTJOIN": {
        "family": "Text",
        "syntax": "TEXTJOIN(delimiter, ignore_empty, text1, [text2], ...)",
        "description": "Combines the text from multiple ranges and/or strings, and includes a delimiter you specify between each text value.",
        "status": "fully_supported"
    },
    "FIND": {
        "family": "Text",
        "syntax": "FIND(find_text, within_text, [start_num])",
        "description": "Finds one text value within another (case-sensitive).",
        "status": "fully_supported"
    },
    "SEARCH": {
        "family": "Text",
        "syntax": "SEARCH(find_text, within_text, [start_num])",
        "description": "Finds one text value within another (not case-sensitive).",
        "status": "fully_supported"
    },
    "SUBSTITUTE": {
        "family": "Text",
        "syntax": "SUBSTITUTE(text, old_text, new_text, [instance_num])",
        "description": "Substitutes new text for old text in a text string.",
        "status": "fully_supported"
    },
    "REPLACE": {
        "family": "Text",
        "syntax": "REPLACE(old_text, start_num, num_chars, new_text)",
        "description": "Replaces characters within text.",
        "status": "fully_supported"
    },
    "TEXT": {
        "family": "Text",
        "syntax": "TEXT(value, format_text)",
        "description": "Formats a number and converts it to text.",
        "status": "fully_supported"
    },
    "VALUE": {
        "family": "Text",
        "syntax": "VALUE(text)",
        "description": "Converts a text argument that represents a number to a number.",
        "status": "fully_supported"
    },
    "EXACT": {
        "family": "Text",
        "syntax": "EXACT(text1, text2)",
        "description": "Checks whether two text values are identical.",
        "status": "fully_supported"
    },

    # Date & Time
    "DATE": {
        "family": "Date & Time",
        "syntax": "DATE(year, month, day)",
        "description": "Returns the serial number of a particular date.",
        "status": "fully_supported"
    },
    "TODAY": {
        "family": "Date & Time",
        "syntax": "TODAY()",
        "description": "Returns the serial number of today's date.",
        "status": "fully_supported"
    },
    "NOW": {
        "family": "Date & Time",
        "syntax": "NOW()",
        "description": "Returns the serial number of the current date and time.",
        "status": "fully_supported"
    },
    "YEAR": {
        "family": "Date & Time",
        "syntax": "YEAR(serial_number)",
        "description": "Converts a serial number to a year.",
        "status": "fully_supported"
    },
    "MONTH": {
        "family": "Date & Time",
        "syntax": "MONTH(serial_number)",
        "description": "Converts a serial number to a month.",
        "status": "fully_supported"
    },
    "DAY": {
        "family": "Date & Time",
        "syntax": "DAY(serial_number)",
        "description": "Converts a serial number to a day of the month.",
        "status": "fully_supported"
    },
    "HOUR": {
        "family": "Date & Time",
        "syntax": "HOUR(serial_number)",
        "description": "Converts a serial number to an hour.",
        "status": "fully_supported"
    },
    "MINUTE": {
        "family": "Date & Time",
        "syntax": "MINUTE(serial_number)",
        "description": "Converts a serial number to a minute.",
        "status": "fully_supported"
    },
    "SECOND": {
        "family": "Date & Time",
        "syntax": "SECOND(serial_number)",
        "description": "Converts a serial number to a second.",
        "status": "fully_supported"
    },
    "EOMONTH": {
        "family": "Date & Time",
        "syntax": "EOMONTH(start_date, months)",
        "description": "Returns the serial number of the last day of the month before or after a specified number of months.",
        "status": "fully_supported"
    },
    "EDATE": {
        "family": "Date & Time",
        "syntax": "EDATE(start_date, months)",
        "description": "Returns the serial number of the date that is the indicated number of months before or after start_date.",
        "status": "fully_supported"
    },
    "DATEDIF": {
        "family": "Date & Time",
        "syntax": "DATEDIF(start_date, end_date, unit)",
        "description": "Calculates the number of days, months, or years between two dates.",
        "status": "fully_supported"
    },
    "WEEKDAY": {
        "family": "Date & Time",
        "syntax": "WEEKDAY(serial_number, [return_type])",
        "description": "Converts a serial number to a day of the week.",
        "status": "fully_supported"
    },
    "WEEKNUM": {
        "family": "Date & Time",
        "syntax": "WEEKNUM(serial_number, [return_type])",
        "description": "Converts a serial number to a number representing where the week falls numerically with a year.",
        "status": "fully_supported"
    },
    "WORKDAY": {
        "family": "Date & Time",
        "syntax": "WORKDAY(start_date, days, [holidays])",
        "description": "Returns the serial number of the date before or after a specified number of workdays.",
        "status": "fully_supported"
    },
    "NETWORKDAYS": {
        "family": "Date & Time",
        "syntax": "NETWORKDAYS(start_date, end_date, [holidays])",
        "description": "Returns the number of whole workdays between two dates.",
        "status": "fully_supported"
    },
    "YEARFRAC": {
        "family": "Date & Time",
        "syntax": "YEARFRAC(start_date, end_date, [basis])",
        "description": "Returns the year fraction representing the number of whole days between start_date and end_date.",
        "status": "fully_supported"
    },
    "DATEVALUE": {
        "family": "Date & Time",
        "syntax": "DATEVALUE(date_text)",
        "description": "Converts a date in the form of text to a serial number.",
        "status": "fully_supported"
    },

    # Statistical
    "MEDIAN": {
        "family": "Statistical",
        "syntax": "MEDIAN(number1, [number2], ...)",
        "description": "Returns the median of the given numbers.",
        "status": "fully_supported"
    },
    "MODE": {
        "family": "Statistical",
        "syntax": "MODE(number1, [number2], ...)",
        "description": "Returns the most common value in a data set.",
        "status": "fully_supported"
    },
    "STDEV.S": {
        "family": "Statistical",
        "syntax": "STDEV.S(number1, [number2], ...)",
        "description": "Estimates standard deviation based on a sample.",
        "status": "fully_supported"
    },
    "STDEV.P": {
        "family": "Statistical",
        "syntax": "STDEV.P(number1, [number2], ...)",
        "description": "Calculates standard deviation based on the entire population.",
        "status": "fully_supported"
    },
    "VAR.S": {
        "family": "Statistical",
        "syntax": "VAR.S(number1, [number2], ...)",
        "description": "Estimates variance based on a sample.",
        "status": "fully_supported"
    },
    "VAR.P": {
        "family": "Statistical",
        "syntax": "VAR.P(number1, [number2], ...)",
        "description": "Calculates variance based on the entire population.",
        "status": "fully_supported"
    },
    "PERCENTILE.INC": {
        "family": "Statistical",
        "syntax": "PERCENTILE.INC(array, k)",
        "description": "Returns the k-th percentile of values in a range.",
        "status": "fully_supported"
    },
    "QUARTILE.INC": {
        "family": "Statistical",
        "syntax": "QUARTILE.INC(array, quart)",
        "description": "Returns the quartile of a data set.",
        "status": "fully_supported"
    },
    "RANK.EQ": {
        "family": "Statistical",
        "syntax": "RANK.EQ(number, ref, [order])",
        "description": "Returns the rank of a number in a list of numbers.",
        "status": "fully_supported"
    },
    "LARGE": {
        "family": "Statistical",
        "syntax": "LARGE(array, k)",
        "description": "Returns the k-th largest value in a data set.",
        "status": "fully_supported"
    },
    "SMALL": {
        "family": "Statistical",
        "syntax": "SMALL(array, k)",
        "description": "Returns the k-th smallest value in a data set.",
        "status": "fully_supported"
    },
    "CORREL": {
        "family": "Statistical",
        "syntax": "CORREL(array1, array2)",
        "description": "Returns the correlation coefficient between two data sets.",
        "status": "fully_supported"
    },
    "COVARIANCE.S": {
        "family": "Statistical",
        "syntax": "COVARIANCE.S(array1, array2)",
        "description": "Returns sample covariance, the average of products of deviations for each data point pair in two data sets.",
        "status": "fully_supported"
    },
    "FORECAST.LINEAR": {
        "family": "Statistical",
        "syntax": "FORECAST.LINEAR(x, known_y's, known_x's)",
        "description": "Calculates, or predicts, a future value along a linear trend by using existing values.",
        "status": "fully_supported"
    },

    # Dynamic Arrays & Modern
    "SEQUENCE": {
        "family": "Dynamic Array",
        "syntax": "SEQUENCE(rows, [columns], [start], [step])",
        "description": "Generates a list of sequential numbers in an array.",
        "status": "fully_supported"
    },
    "TAKE": {
        "family": "Dynamic Array",
        "syntax": "TAKE(array, rows, [columns])",
        "description": "Returns a contiguous subset of rows or columns from an array.",
        "status": "fully_supported"
    },
    "DROP": {
        "family": "Dynamic Array",
        "syntax": "DROP(array, rows, [columns])",
        "description": "Excludes a specified number of rows or columns from the start or end of an array.",
        "status": "fully_supported"
    },
    "CHOOSECOLS": {
        "family": "Dynamic Array",
        "syntax": "CHOOSECOLS(array, col_num1, [col_num2], ...)",
        "description": "Returns the specified columns from an array.",
        "status": "fully_supported"
    },
    "CHOOSEROWS": {
        "family": "Dynamic Array",
        "syntax": "CHOOSEROWS(array, row_num1, [row_num2], ...)",
        "description": "Returns the specified rows from an array.",
        "status": "fully_supported"
    },
    "HSTACK": {
        "family": "Dynamic Array",
        "syntax": "HSTACK(array1, [array2], ...)",
        "description": "Appends arrays horizontally and in sequence to return a larger array.",
        "status": "fully_supported"
    },
    "VSTACK": {
        "family": "Dynamic Array",
        "syntax": "VSTACK(array1, [array2], ...)",
        "description": "Appends arrays vertically and in sequence to return a larger array.",
        "status": "fully_supported"
    },
    "LET": {
        "family": "Dynamic Array",
        "syntax": "LET(name1, name_value1, calculation_or_name2, ...)",
        "description": "Assigns names to calculation results.",
        "status": "partially_supported"
    }
}
