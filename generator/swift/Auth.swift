import UIKit
import WebKit

import Security

import Foundation

public class DropboxAccessToken : Printable {
    var accessToken: String
    var uid: String
    
    init(accessToken: String, uid: String) {
        self.accessToken = accessToken
        self.uid = uid
    }
    
    public var description : String {
        return self.accessToken
    }
}

public enum OAuth2Error {
    case UnauthorizedClient
    case AccessDenied
    case UnsupportedResponseType
    case InvalidScope
    case ServerError
    case TemporarilyUnavailable
    case Unknown
    
    init(errorCode: String) {
        switch errorCode {
            case "unauthorized_client": self = .UnauthorizedClient
            case "access_denied": self = .AccessDenied
            case "unsupported_response_type": self = .UnsupportedResponseType
            case "invalid_scope": self = .InvalidScope
            case "server_error": self = .ServerError
            case "temporarily_unavailable": self = .TemporarilyUnavailable
            default: self = .Unknown
        }
    }
}

public enum DropboxAuthResult {
    case Success(DropboxAccessToken)
    case Error(OAuth2Error, String)
}

private class Keychain {
    class func set(#key: String, value: String) -> Bool {
        if let data = value.dataUsingEncoding(NSUTF8StringEncoding) {
            return set(key: key, value: data)
        } else {
            return false
        }
    }
    
    class func set(#key: String, value: NSData) -> Bool {
        let query : CFDictionaryRef = [
            (      kSecClass as! String): kSecClassGenericPassword,
            (kSecAttrAccount as! String): key,
            (  kSecValueData as! String): value
        ]
        
        SecItemDelete(query)
        
        return SecItemAdd(query, nil) == noErr
    }
    
    class func getAsData(key: String) -> NSData? {
        let query : CFDictionaryRef = [
            (      kSecClass as! String): kSecClassGenericPassword,
            (kSecAttrAccount as! String): key,
            ( kSecReturnData as! String): kCFBooleanTrue,
            ( kSecMatchLimit as! String): kSecMatchLimitOne
        ]
        
        var dataTypeRef : Unmanaged<AnyObject>?
        let status = SecItemCopyMatching(query, &dataTypeRef)
        
        if status == noErr {
            return dataTypeRef?.takeRetainedValue() as? NSData
        }
        
        return nil
    }
    
    class func getAll() -> [String] {
        let query : CFDictionaryRef = [
            (            kSecClass as! String): kSecClassGenericPassword,
            ( kSecReturnAttributes as! String): kCFBooleanTrue,
            (       kSecMatchLimit as! String): kSecMatchLimitAll
        ]
        
        var dataTypeRef : Unmanaged<AnyObject>?
        let status = SecItemCopyMatching(query, &dataTypeRef)
        
        if status == noErr {
            let results = dataTypeRef?.takeRetainedValue() as! [[String : AnyObject]]
            
            return results.map { d in d["acct"] as! String }
        
        }
        return []
    }
    

    
    class func get(key: String) -> String? {
        if let data = getAsData(key) {
            return NSString(data: data, encoding: NSUTF8StringEncoding) as? String
        } else {
            return nil
        }
    }
    
    class func delete(key: String) -> Bool {
        let query : CFDictionaryRef = [
            (kSecClass as! String) : kSecClassGenericPassword,
            (kSecAttrAccount as! String): key
        ]
        
        return SecItemDelete(query) == noErr
    }
    
    class func clear() -> Bool {
        let query : CFDictionaryRef = [
            (kSecClass as! String) : kSecClassGenericPassword,
        ]
        
        return SecItemDelete(query) == noErr
    }
}

public class DropboxAuthManager {
    
    let appKey : String
    let redirectURL: NSURL
    let host: String
    
    
    public static var sharedAuthManager : DropboxAuthManager!
    
    
    public init(appKey: String, host: String) {
        self.appKey = appKey
        self.host = host
        self.redirectURL = NSURL(string: "db-\(self.appKey)://2/token")!
    }
    
    convenience public init(appKey: String) {
        self.init(appKey: appKey, host: "www.dropbox.com")
    }
    
    func authURL() -> NSURL {

        let components = NSURLComponents()
        components.scheme = "https"
        components.host = self.host
        components.path = "/1/oauth2/authorize"

        components.queryItems = [
            NSURLQueryItem(name: "response_type", value: "token"),
            NSURLQueryItem(name: "client_id", value: self.appKey),
            NSURLQueryItem(name: "redirect_uri", value: self.redirectURL.URLString)
        ]
        
        return components.URL!
    }
    
    private func canHandleURL(url: NSURL) -> Bool {
        return (url.scheme == self.redirectURL.scheme
            &&  url.host == self.redirectURL.host
            &&  url.path == self.redirectURL.path)
    }
    
    
    public func authorizeFromController(controller: UIViewController) {
        let web = DropboxConnectController(
            URL: self.authURL(),
            tryIntercept: { url in
                if self.canHandleURL(url) {
                    UIApplication.sharedApplication().openURL(url)
                    return true
                } else {
                    return false
                }
            }
        )
        
        let navigationController = UINavigationController(rootViewController: web)
        controller.presentViewController(navigationController, animated: true, completion: nil)
    }
    
    public func handleRedirectURL(url: NSURL) -> DropboxAuthResult? {
        if !self.canHandleURL(url) {
            return nil
        }
        
        var results = [String: String]()
        let pairs  = url.fragment?.componentsSeparatedByString("&") ?? []
        
        for pair in pairs {
            let kv = pair.componentsSeparatedByString("=")
            results.updateValue(kv[1], forKey: kv[0])
        }
        
        if let error = results["error"] {
            let desc = results["error_description"]?.stringByReplacingOccurrencesOfString("+", withString: " ").stringByReplacingPercentEscapesUsingEncoding(NSASCIIStringEncoding)
            return .Error(OAuth2Error(errorCode: error), desc ?? "")
        } else {
            let accessToken = results["access_token"]!
            let uid = results["uid"]!
        
            Keychain.set(key: uid, value: accessToken)
            return .Success(DropboxAccessToken(accessToken: accessToken, uid: uid))
        }
    }
    
    public func getAllAccessTokens() -> [String : DropboxAccessToken] {
        let users = Keychain.getAll()
        var ret = [String : DropboxAccessToken]()
        for user in users {
            if let accessToken = Keychain.get(user) {
                ret[user] = DropboxAccessToken(accessToken: accessToken, uid: user)
            }
        }
        return ret
    }
    
    public func hasStoredAccessTokens() -> Bool {
        return self.getAllAccessTokens().count != 0
    }
    
    public func getAccessToken(#user: String) -> DropboxAccessToken? {
        if let accessToken = Keychain.get(user) {
            return DropboxAccessToken(accessToken: accessToken, uid: user)
        } else {
            return nil
        }
    }
    
    public func clearStoredAccessToken(token: DropboxAccessToken) -> Bool {
        return Keychain.delete(token.uid)
    }
    
    public func clearStoredAccessTokens() -> Bool {
        return Keychain.clear()
    }
    
    public func storeAccessToken(token: DropboxAccessToken) -> Bool {
        return Keychain.set(key: token.uid, value: token.accessToken)
    }
    
    public func getFirstAccessToken() -> DropboxAccessToken? {
        return self.getAllAccessTokens().values.first
    }
}


public class DropboxConnectController : UIViewController, WKNavigationDelegate {
    var webView : WKWebView!
    
    var onWillDismiss: ((didCancel: Bool) -> Void)?
    var tryIntercept: ((url: NSURL) -> Bool)?
    
    var cancelButton: UIBarButtonItem?
    
    
    public init() {
        super.init(nibName: nil, bundle: nil)
    }
    
    public init(URL: NSURL, tryIntercept: ((url: NSURL) -> Bool)) {
        super.init(nibName: nil, bundle: nil)
        self.startURL = URL
        self.tryIntercept = tryIntercept
    }
    
    required public init(coder aDecoder: NSCoder) {
        super.init(coder: aDecoder)
    }
    
    override public func viewDidLoad() {
        super.viewDidLoad()
        self.title = "Link to Dropbox"
        self.webView = WKWebView(frame: self.view.bounds)
        self.view.addSubview(self.webView)
        
        self.webView.navigationDelegate = self
        
        self.view.backgroundColor = UIColor.whiteColor()
        
        self.cancelButton = UIBarButtonItem(barButtonSystemItem: .Cancel, target: self, action: "cancel:")
        self.navigationItem.rightBarButtonItem = self.cancelButton
    }
    
    public override func viewWillAppear(animated: Bool) {
        super.viewWillAppear(animated)
        if !webView.canGoBack {
            if nil != startURL {
                loadURL(startURL!)
            }
            else {
                webView.loadHTMLString("There is no `startURL`", baseURL: nil)
            }
        }
    }
    
    public func webView(webView: WKWebView,
        decidePolicyForNavigationAction navigationAction: WKNavigationAction,
        decisionHandler: (WKNavigationActionPolicy) -> Void) {
        if let url = navigationAction.request.URL, callback = self.tryIntercept {
            if callback(url: url) {
                self.dismiss(animated: true)
                return decisionHandler(.Cancel)
            }
        }
        return decisionHandler(.Allow)
    }
    
    public var startURL: NSURL? {
        didSet(oldURL) {
            if nil != startURL && nil == oldURL && isViewLoaded() {
                loadURL(startURL!)
            }
        }
    }
    
    public func loadURL(url: NSURL) {
        webView.loadRequest(NSURLRequest(URL: url))
    }
    
    func showHideBackButton(show: Bool) {
        navigationItem.leftBarButtonItem = show ? UIBarButtonItem(barButtonSystemItem: .Rewind, target: self, action: "goBack:") : nil
    }
    
    func goBack(sender: AnyObject?) {
        webView.goBack()
    }
    
    func cancel(sender: AnyObject?) {
        dismiss(asCancel: true, animated: (sender != nil))
    }
    
    func dismiss(#animated: Bool) {
        dismiss(asCancel: false, animated: animated)
    }
    
    func dismiss(#asCancel: Bool, animated: Bool) {
        webView.stopLoading()
        
        self.onWillDismiss?(didCancel: asCancel)
        presentingViewController?.dismissViewControllerAnimated(animated, completion: nil)
    }
    
}