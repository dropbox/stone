import SwiftyJSON

public protocol JSONSerializer {
	typealias ValueType
	func serialize(ValueType) -> String?
    func deserialize(JSON) -> ValueType
}

class ArraySerializer<T : JSONSerializer> : JSONSerializer {

	var elementSerializer : T

	init(_ elementSerializer: T) {
		self.elementSerializer = elementSerializer
	}

	func serialize(arr : Array<T.ValueType>) -> String? {
		let s = ", ".join(arr.map { self.elementSerializer.serialize($0) ?? "null" })
		return "[\(s)]"
	}

    func deserialize(json : JSON) -> Array<T.ValueType> {
        var out : Array<T.ValueType> = []

        for (index : String, subjson : JSON) in json {
            out.append(self.elementSerializer.deserialize(subjson))
        }
        return out
    }
}

class StringSerializer : JSONSerializer {
    func serialize(value : String) -> String? {
        return "\"\(value)\""
    }

    func deserialize(json: JSON) -> String {
        return json.stringValue
    }
}

class NSDateSerializer : JSONSerializer {

	var dateFormatter : NSDateFormatter

    private func convertFormat(format: String) -> String? {
        func symbolForToken(token: String) -> String {
            switch token {
            case "%a": // Weekday as locale’s abbreviated name.
                return "EEE"
            case "%A": // Weekday as locale’s full name.
                return "EEEE"
            case "%w": // Weekday as a decimal number, where 0 is Sunday and 6 is Saturday. 0, 1, ..., 6
                return "ccccc"
            case "%d": // Day of the month as a zero-padded decimal number. 01, 02, ..., 31
                return "dd"
            case "%b": // Month as locale’s abbreviated name.
                return "MMM"
            case "%B": // Month as locale’s full name.
                return "MMMM"
            case "%m": // Month as a zero-padded decimal number. 01, 02, ..., 12
                return "MM"
            case "%y": // Year without century as a zero-padded decimal number. 00, 01, ..., 99
                return "yy"
            case "%Y": // Year with century as a decimal number. 1970, 1988, 2001, 2013
                return "yyyy"
            case "%H": // Hour (24-hour clock) as a zero-padded decimal number. 00, 01, ..., 23
                return "HH"
            case "%I": // Hour (12-hour clock) as a zero-padded decimal number. 01, 02, ..., 12
                return "hh"
            case "%p": // Locale’s equivalent of either AM or PM.
                return "a"
            case "%M": // Minute as a zero-padded decimal number. 00, 01, ..., 59
                return "mm"
            case "%S": // Second as a zero-padded decimal number. 00, 01, ..., 59
                return "ss"
            case "%f": // Microsecond as a decimal number, zero-padded on the left. 000000, 000001, ..., 999999
                return "SSSSSS"
            case "%z": // UTC offset in the form +HHMM or -HHMM (empty string if the the object is naive). (empty), +0000, -0400, +1030
                return "Z"
            case "%Z": // Time zone name (empty string if the object is naive). (empty), UTC, EST, CST
                return "z"
            case "%j": // Day of the year as a zero-padded decimal number. 001, 002, ..., 366
                return "DDD"
            case "%U": // Week number of the year (Sunday as the first day of the week) as a zero padded decimal number. All days in a new year preceding the first Sunday are considered to be in week 0. 00, 01, ..., 53 (6)
                return "ww"
            case "%W": // Week number of the year (Monday as the first day of the week) as a decimal number. All days in a new year preceding the first Monday are considered to be in week 0. 00, 01, ..., 53 (6)
                return "ww" // one of these can't be right
            case "%c": // Locale’s appropriate date and time representation.
                return "" // unsupported
            case "%x": // Locale’s appropriate date representation.
                return "" // unsupported
            case "%X": // Locale’s appropriate time representation.
                return "" // unsupported
            case "%%": // A literal '%' character.
                return "%"
            default:
                return ""
            }
        }
        var newFormat = ""
        var inQuotedText = false
        var i = format.startIndex
        while i < format.endIndex {
            if format[i] == "%" {
                if i.successor() >= format.endIndex {
                    return nil
                }
                i = i.successor()
                let token = "%\(format[i])"
                if inQuotedText {
                    newFormat += "'"
                    inQuotedText = false
                }
                newFormat += symbolForToken(token)
            } else {
                if contains("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", format[i]) {
                    if !inQuotedText {
                        newFormat += "'"
                        inQuotedText = true
                    }
                } else if format[i] == "'" {
                    newFormat += "'"
                }
                newFormat += String(format[i])
            }
            i = i.successor()
        }
        if inQuotedText {
            newFormat += "'"
        }
        return newFormat
    }


	init(_ dateFormat: String) {
		self.dateFormatter = NSDateFormatter()
		dateFormatter.dateFormat = self.convertFormat(dateFormat)
	}
    func serialize(value: NSDate) -> String? {
		return "\"\(self.dateFormatter.stringFromDate(value))\""
    }

    func deserialize(json: JSON) -> NSDate {
        return self.dateFormatter.dateFromString(json.stringValue)!
    }
}

class BoolSerializer : JSONSerializer {
    func serialize(value : Bool) -> String? {
        return value ? "true" : "false"
    }
    func deserialize(json : JSON) -> Bool {
        return json.boolValue
    }
}

class UInt64Serializer : JSONSerializer {
    func serialize(value : UInt64) -> String? {
        return String(value)
    }

    func deserialize(json : JSON) -> UInt64 {
        return json.numberValue.unsignedLongLongValue
    }
}

class NullableSerializer<T : JSONSerializer> : JSONSerializer {

	var internalSerializer : T

	init(_ serializer : T) {
		self.internalSerializer = serializer
	}

	func serialize(value : Optional<T.ValueType>) -> String? {
		if let v = value {
			return internalSerializer.serialize(v)
		} else {
			return nil
		}
	}

    func deserialize(json: JSON) -> Optional<T.ValueType> {
        if let val = json.null {
            return nil
        } else {
            return internalSerializer.deserialize(json)
        }
    }
}

struct Serialization {
	static var _StringSerializer = StringSerializer()
	static var _BoolSerializer = BoolSerializer()
	static var _UInt64Serializer = UInt64Serializer()

	static func addOutput<T : JSONSerializer>(#field: String, value : T.ValueType, serializer : T, inout output : [String]) {
		if let v = serializer.serialize(value) {
			output.append("\"\(field)\": \(v)")
		}
	}

	static func output<T : JSONSerializer>(#field: String, value : T.ValueType, serializer : T) -> String? {
		let v = serializer.serialize(value) ?? "null"
		return "\"\(field)\": \(v)"
	}
}


