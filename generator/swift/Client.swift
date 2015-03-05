//
//  Dropbox.swift
//  Dropbox
//
//  Created by Leah Culver on 10/9/14.
//  Copyright (c) 2014 Dropbox. All rights reserved.
//

import Foundation
import Alamofire
import SwiftyJSON

// Dropbox API errors
public let DropboxErrorDomain = "com.dropbox.error"

public class Box<T> {
	public let unboxed : T
	init (_ v : T) { self.unboxed = v }
}
public enum CallError<ErrorType> {
    case InternalServerError(Int, String?)
    case BadInputError(String?)
    case RateLimitError
    case HTTPError(Int?, String?)
    case RouteError(Box<ErrorType>)
}

public class DropboxRequest<RType : JSONSerializer, EType : JSONSerializer> {
    let errorSerializer : EType
    let responseSerializer : RType
    let request : Request
    
    init(client: DropboxClient,
        host: String,
        route: String,
        params: String?,
        responseSerializer: RType,
        errorSerializer: EType,
        requestEncoder: (URLRequestConvertible, [String: AnyObject]?) -> (NSURLRequest, NSError?)) {
            self.errorSerializer = errorSerializer
            self.responseSerializer = responseSerializer
            let url = "\(client.baseHosts[host]!)\(route)"
            self.request = Alamofire.request(.POST, url, parameters: [:], encoding: .Custom(requestEncoder))
    }
    
    func handleResponseError(response: NSHTTPURLResponse?, data: NSData) -> CallError<EType.ValueType> {
        if let code = response?.statusCode {
            switch code {
            case 500...599:
                let message = NSString(data: data, encoding: NSUTF8StringEncoding)
                return .InternalServerError(code, message)
            case 400:
                let message = NSString(data: data, encoding: NSUTF8StringEncoding)
                return .BadInputError(message)
            case 429:
                 return .RateLimitError
            case 409:
                let json = JSON(data: data)
                return .RouteError(Box(self.errorSerializer.deserialize(json["reason"])))
            default:
                return .HTTPError(code, "An error occurred.")
            }
        } else {
            let message = NSString(data: data, encoding: NSUTF8StringEncoding)
            return .HTTPError(nil, message)
        }
    }
}


public class DropboxRpcRequest<RType : JSONSerializer, EType : JSONSerializer> : DropboxRequest<RType, EType> {
    
    init(client: DropboxClient, host: String, route: String, params: String?, responseSerializer: RType, errorSerializer: EType) {
        super.init( client: client, host: host, route: route, params: params, responseSerializer: responseSerializer, errorSerializer: errorSerializer,
        requestEncoder: ({ convertible, _ in
            var mutableRequest = convertible.URLRequest.copy() as NSMutableURLRequest
            mutableRequest.addValue("application/json", forHTTPHeaderField: "Content-Type")
            if let p = params {
                mutableRequest.HTTPBody = p.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: false)
            }
            return (mutableRequest, nil)
        }))
    }
    
    
    public func response(completionHandler: (RType.ValueType?, CallError<EType.ValueType>?) -> Void) -> Self {
        self.request.validate().response {
            (request, response, dataObj, error) -> Void in
            let data = dataObj as NSData
            if error != nil {
                completionHandler(nil, self.handleResponseError(response, data: data))
            } else {
                completionHandler(self.responseSerializer.deserialize(JSON(data: data)), nil)
            }
        }
        return self
    }
}

public class DropboxUploadRequest<RType : JSONSerializer, EType : JSONSerializer> : DropboxRequest<RType, EType> {
    init(client: DropboxClient, host: String, route: String, params: String?, body: NSData, responseSerializer: RType, errorSerializer: EType) {
        super.init( client: client, host: host, route: route, params: params, responseSerializer: responseSerializer, errorSerializer: errorSerializer,
        requestEncoder: ({ convertible, _ in
            var mutableRequest = convertible.URLRequest.copy() as NSMutableURLRequest
            mutableRequest.addValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
            mutableRequest.HTTPBody = body
            
            if let p = params {
                mutableRequest.addValue(p, forHTTPHeaderField: "Dropbox-Api-Arg")
            }
            return (mutableRequest, nil)
        }))
    }
    
    public func progress(closure: ((Int64, Int64, Int64) -> Void)? = nil) -> Self {
        self.request.progress(closure)
        return self
    }
    
    public func response(completionHandler: (RType.ValueType?, CallError<EType.ValueType>?) -> Void) -> Self {
        self.request.validate().response {
            (request, response, dataObj, error) -> Void in
            let data = dataObj as NSData
            if error != nil {
                completionHandler(nil, self.handleResponseError(response, data: data))
            } else {
                completionHandler(self.responseSerializer.deserialize(JSON(data: data)), nil)
            }
        }
        return self
    }

}

public class DropboxDownloadRequest<RType : JSONSerializer, EType : JSONSerializer> : DropboxRequest<RType, EType> {
    init(client: DropboxClient, host: String, route: String, params: String?, responseSerializer: RType, errorSerializer: EType) {
        super.init( client: client, host: host, route: route, params: params, responseSerializer: responseSerializer, errorSerializer: errorSerializer,
        requestEncoder: ({ convertible, _ in
            var mutableRequest = convertible.URLRequest.copy() as NSMutableURLRequest
            if let p = params {
                mutableRequest.addValue(p, forHTTPHeaderField: "Dropbox-Api-Arg")
            }
            return (mutableRequest, nil)
        }))
    }
    
    public func progress(closure: ((Int64, Int64, Int64) -> Void)? = nil) -> Self {
        self.request.progress(closure)
        return self
    }
    
    public func response(completionHandler: ( (RType.ValueType, NSData)?, CallError<EType.ValueType>?) -> Void) -> Self {
        self.request.validate().response {
            (request, response, dataObj, error) -> Void in
            let data = dataObj as NSData
            if error != nil {
                completionHandler(nil, self.handleResponseError(response, data: data))
            } else {
                let result = response!.allHeaderFields["Dropbox-Api-Result"] as String
                let resultData = result.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: false)!
                let resultObject = self.responseSerializer.deserialize(JSON(data: resultData))
                
                completionHandler( (resultObject, data), nil)
            }
        }
        return self
    }
}

public class DropboxClient {
    var accessToken: String
    var baseHosts : [String : String]
    
    
    public init(accessToken: String, baseApiUrl: String, baseContentUrl: String, baseNotifyUrl: String) {
        self.accessToken = accessToken
        self.baseHosts = [
            "meta" : baseApiUrl,
            "content": baseContentUrl,
            "notify": baseNotifyUrl,
        ]
        
        // Authentication header with access token
        Manager.sharedInstance.session.configuration.HTTPAdditionalHeaders = [
            "Authorization" : "Bearer \(accessToken)",
        ]
    }
    
    public convenience init(accessToken: String) {
        self.init(accessToken: accessToken,
            baseApiUrl: "https://api.dropbox.com/2-beta",
            baseContentUrl: "https://api-content.dropbox.com/2-beta",
            baseNotifyUrl: "https://api-notify.dropbox.com")
    }
    
    func runRpcRequest<RType: JSONSerializer, EType: JSONSerializer>(#host: String, route: String, params: String?,responseSerializer: RType, errorSerializer: EType) -> DropboxRpcRequest<RType, EType> {
        return DropboxRpcRequest(client: self, host: host, route: route, params: params, responseSerializer: responseSerializer, errorSerializer: errorSerializer)
    }
    
    func runUploadRequest<RType: JSONSerializer, EType: JSONSerializer>(#host: String, route: String, params: String?, body: NSData, responseSerializer: RType, errorSerializer: EType) -> DropboxUploadRequest<RType, EType> {
        return DropboxUploadRequest(client: self, host: host, route: route, params: params, body: body, responseSerializer: responseSerializer, errorSerializer: errorSerializer)
    }
    func runDownloadRequest<RType: JSONSerializer, EType: JSONSerializer>(#host: String, route: String, params: String?,responseSerializer: RType, errorSerializer: EType) -> DropboxDownloadRequest<RType, EType> {
        return DropboxDownloadRequest(client: self, host: host, route: route, params: params, responseSerializer: responseSerializer, errorSerializer: errorSerializer)
    }

}





