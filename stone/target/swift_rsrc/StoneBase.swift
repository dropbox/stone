import Foundation

// The objects in this file are used by generated code and should not need to be invoked manually.

public class Route<ASerial: JSONSerializer, RSerial: JSONSerializer, ESerial: JSONSerializer> {
    public let name: String
    public let namespace: String
    public let deprecated: Bool
    public let argSerializer: ASerial
    public let responseSerializer: RSerial
    public let errorSerializer: ESerial
    public let attrs: [String: String?]

    public init(name: String, namespace: String, deprecated: Bool, argSerializer: ASerial,
                responseSerializer: RSerial, errorSerializer: ESerial, attrs: [String: String?]) {
        self.name = name
        self.namespace = namespace
        self.deprecated = deprecated
        self.argSerializer = argSerializer
        self.responseSerializer = responseSerializer
        self.errorSerializer = errorSerializer
        self.attrs = attrs
    }
}

public class Box<T> {
    public let unboxed: T
    init (_ v: T) { self.unboxed = v }
}

public enum CallError<EType>: CustomStringConvertible {
    case InternalServerError(Int, String?, String?)
    case BadInputError(String?, String?)
    case RateLimitError
    case HTTPError(Int?, String?, String?)
    case RouteError(Box<EType>, String?)
    case OSError(ErrorType?)
    
    public var description: String {
        switch self {
        case let .InternalServerError(code, message, requestId):
            var ret = ""
            if let r = requestId {
                ret += "[request-id \(r)] "
            }
            ret += "Internal Server Error \(code)"
            if let m = message {
                ret += ": \(m)"
            }
            return ret
        case let .BadInputError(message, requestId):
            var ret = ""
            if let r = requestId {
                ret += "[request-id \(r)] "
            }
            ret += "Bad Input"
            if let m = message {
                ret += ": \(m)"
            }
            return ret
        case .RateLimitError:
            return "Rate limited"
        case let .HTTPError(code, message, requestId):
            var ret = ""
            if let r = requestId {
                ret += "[request-id \(r)] "
            }
            ret += "HTTP Error"
            if let c = code {
                ret += "\(c)"
            }
            if let m = message {
                ret += ": \(m)"
            }
            return ret
        case let .RouteError(box, requestId):
            var ret = ""
            if let r = requestId {
                ret += "[request-id \(r)] "
            }
            ret += "API route error - \(box.unboxed)"
            return ret
        case let .OSError(err):
            if let e = err {
                return "\(e)"
            }
            return "An unknown system error"
        }
    }
}

func utf8Decode(data: NSData) -> String {
    return NSString(data: data, encoding: NSUTF8StringEncoding)! as String
}

func asciiEscape(s: String) -> String {
    var out: String = ""

    for char in s.unicodeScalars {
        var esc = "\(char)"
        if !char.isASCII() {
            esc = NSString(format:"\\u%04x", char.value) as String
        } else {
            esc = "\(char)"
        }
        out += esc
        
    }
    return out
}