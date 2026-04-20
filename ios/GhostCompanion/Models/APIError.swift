import Foundation

enum APIError: Error, LocalizedError {
    case invalidURL
    case network(URLError)
    case http(Int, String?)
    case unauthorized
    case decode(Error)
    case stream(String)
    case cancelled

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "Invalid server URL."
        case .network(let err): return "Network error: \(err.localizedDescription)"
        case .http(let code, let msg):
            if let msg, !msg.isEmpty { return "Server returned \(code): \(msg)" }
            return "Server returned \(code)."
        case .unauthorized: return "Session expired. Please sign in again."
        case .decode: return "Couldn't understand server response."
        case .stream(let msg): return msg
        case .cancelled: return "Request cancelled."
        }
    }
}
