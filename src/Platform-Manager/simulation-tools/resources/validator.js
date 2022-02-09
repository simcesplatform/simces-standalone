/* jshint esversion: 6 */

const ucum = require("@lhncbc/ucum-lhc");
const ucumUtils = ucum.UcumLhcUtils.getInstance();

const validText = "valid";
const resultSeparator = ";";

function validate_ucum_code(unit_code) {
    // Uses the ucum-lhc library to validate the given unit_code as a valid UCUM unit code.
    const result = ucumUtils.validateUnitString(unit_code, false);
    var description = "";
    if (result.status === validText) {
        description = result.unit.name;
    }

    return [result.status, description].join(resultSeparator);
}

// Use the first command line parameter as the unit code to be validated and write result to the condole.
console.log(validate_ucum_code(process.argv[2]));
