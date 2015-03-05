protocol Validator {
    typealias ValueType
    func validate(value: ValueType)
}

class ArrayValidator<T: Validator>: Validator {
    let itemValidator: T
    let minItems : Int?
    let maxItems : Int?

    init(itemValidator: T, minItems : Int? = nil, maxItems : Int? = nil) {
        self.itemValidator = itemValidator
        self.minItems = minItems
        self.maxItems = maxItems
    }

    func validate(value : Array<T.ValueType>) {

        if let min = self.minItems {
            assert (value.count >= min, "\(value) must have at least \(min) items")
        }

        if let max = self.maxItems {
            assert (value.count <= max, "\(value) must have at most \(max) items")
        }

        for el in value {
            self.itemValidator.validate(el)
        }
    }
}

class StringValidator : Validator {

    let minLength : Int?
    let maxLength : Int?
    let regex : NSRegularExpression?

    init(minLength : Int? = nil, maxLength : Int? = nil, pattern: String? = nil) {
        self.minLength = minLength
        self.maxLength = maxLength

        if let pat = pattern {
            self.regex = NSRegularExpression(pattern: pat,
                                             options: nil,
                                             error: nil)
        }
    }

    func validate(value : String) {
        let length = countElements(value)
        if let min = self.minLength {
            assert(length >= min, "\"\(value)\" must be at least \(min) characters")
        }

        if let max = self.maxLength {
            assert (length <= max, "\"\(value)\" must be at most \(max) characters")
        }

        if let re = self.regex {
            let matches = re.matchesInString(value, options: nil, range: NSMakeRange(0, length))
            assert(matches.count > 0, "\"\(value) must match pattern \"\(re.pattern)\"")
        }
    }
}

class ComparableTypeValidator<T : Comparable> : Validator {
    let minValue : T?
    let maxValue : T?

    init(minValue : T? = nil, maxValue : T? = nil) {
        self.minValue = minValue
        self.maxValue = maxValue
    }

    func validate(value : T) {
        if let min = self.minValue {
            assert (min <= value, "\(value) must be at least \(min)")
        }
        if let max = self.maxValue {
            assert (max >= value, "\(value) must be at most \(max)")
        }
    }
}

class NullableValidator<T : Validator> : Validator {
    let internalValidator : T

    init(_ internalValidator : T) {
        self.internalValidator = internalValidator
    }

    func validate(value : Optional<T.ValueType>) {
        if let v = value {
            self.internalValidator.validate(v)
        }
    }
}

class EmptyValidator<T> : Validator {
    func validate(value : T) { }
}
