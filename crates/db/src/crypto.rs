use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, AeadCore, Nonce,
};
use anyhow::{anyhow, Context};
use hkdf::Hkdf;
use sha2::Sha256;

const NONCE_LEN: usize = 12;
/// Application-specific salt for HKDF key derivation.
/// Used as both the HKDF extract salt and expand info to bind derived keys
/// to this application context.
pub const APP_SALT: &[u8] = b"ghost-companion-token-encryption-v1";

/// Derives a 32-byte AES-256 key from an arbitrary-length passphrase using
/// HKDF-SHA256 with a fixed application-specific salt.
pub fn derive_key(passphrase: &[u8], salt: &[u8]) -> [u8; 32] {
    let hk = Hkdf::<Sha256>::new(Some(salt), passphrase);
    let mut key = [0u8; 32];
    // info is our app salt so different applications sharing a passphrase
    // still derive distinct keys.
    hk.expand(APP_SALT, &mut key)
        .expect("32-byte output is a valid length for HKDF-SHA256");
    key
}

/// Encrypts `plaintext` with AES-256-GCM using the provided 32-byte key.
///
/// Returns `nonce (12 bytes) || ciphertext`.
pub fn encrypt(plaintext: &str, key: &[u8; 32]) -> Result<Vec<u8>, anyhow::Error> {
    let cipher = Aes256Gcm::new(key.into());
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let ciphertext = cipher
        .encrypt(&nonce, plaintext.as_bytes())
        .map_err(|e| anyhow!("encryption failed: {e}"))?;

    let mut output = Vec::with_capacity(NONCE_LEN + ciphertext.len());
    output.extend_from_slice(&nonce);
    output.extend_from_slice(&ciphertext);
    Ok(output)
}

/// Decrypts a blob previously produced by [`encrypt`].
///
/// Expects the first 12 bytes to be the nonce, followed by the ciphertext.
pub fn decrypt(data: &[u8], key: &[u8; 32]) -> Result<String, anyhow::Error> {
    if data.len() < NONCE_LEN {
        return Err(anyhow!(
            "ciphertext too short: expected at least {NONCE_LEN} bytes, got {}",
            data.len()
        ));
    }

    let (nonce_bytes, ciphertext) = data.split_at(NONCE_LEN);
    let nonce = Nonce::from_slice(nonce_bytes);

    let cipher = Aes256Gcm::new(key.into());
    let plaintext = cipher
        .decrypt(nonce, ciphertext)
        .map_err(|e| anyhow!("decryption failed: {e}"))?;

    String::from_utf8(plaintext).context("decrypted payload is not valid UTF-8")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_key() -> [u8; 32] {
        derive_key(b"test-passphrase", b"test-salt")
    }

    #[test]
    fn round_trip_encrypt_decrypt() {
        let key = test_key();
        let original = "my-secret-access-token-value";

        let encrypted = encrypt(original, &key).expect("encryption should succeed");
        let decrypted = decrypt(&encrypted, &key).expect("decryption should succeed");

        assert_eq!(decrypted, original);
    }

    #[test]
    fn decrypt_with_wrong_key_fails() {
        let key = test_key();
        let wrong_key = derive_key(b"wrong-passphrase", b"wrong-salt");
        let encrypted = encrypt("secret", &key).expect("encryption should succeed");

        let result = decrypt(&encrypted, &wrong_key);
        assert!(result.is_err(), "decryption with wrong key must fail");
    }

    #[test]
    fn decrypt_truncated_ciphertext_fails() {
        let key = test_key();

        // Too short to even contain a nonce
        let result = decrypt(&[0u8; 5], &key);
        assert!(result.is_err(), "truncated ciphertext must fail");

        // Has nonce but ciphertext is corrupted/truncated
        let encrypted = encrypt("hello", &key).expect("encryption should succeed");
        let truncated = &encrypted[..NONCE_LEN + 1]; // nonce + 1 garbage byte
        let result = decrypt(truncated, &key);
        assert!(result.is_err(), "truncated ciphertext body must fail");
    }
}
