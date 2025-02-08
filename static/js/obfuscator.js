const obfuscator = {
    charMap: {
        '=': '_eq_',
        '/': '_sl_',
        '+': '_pl_',
        '&': '_am_',
        '%': '_pc_',
        '#': '_hs_',
        '@': '_at_',
        '.': '_dt_',
        ',': '_cm_',
        ';': '_sc_',
        ':': '_cl_',
        '!': '_ex_'
    },

    encode: function(code) {
        if (!code || typeof code !== 'string') {
            return '';
        }

        try {
            // Replace special characters first
            let processed = code;
            for (const [char, replacement] of Object.entries(this.charMap)) {
                processed = processed.split(char).join(replacement);
            }

            // Convert to base64
            const base64 = btoa(unescape(encodeURIComponent(processed)));
            
            // Additional scrambling
            return base64.split('').reverse().join('') + 
                   '_' + 
                   Date.now().toString(36);
        } catch (error) {
            console.error('Encoding error:', error);
            return '';
        }
    },

    decode: function(encoded) {
        if (!encoded || typeof encoded !== 'string') {
            return '';
        }

        try {
            // Remove timestamp
            const actualData = encoded.split('_')[0];
            
            // Reverse the string back
            const reversed = actualData.split('').reverse().join('');
            
            // Decode from base64
            let decoded = decodeURIComponent(escape(atob(reversed)));
            
            // Replace back special characters
            for (const [char, replacement] of Object.entries(this.charMap)) {
                decoded = decoded.split(replacement).join(char);
            }
            
            return decoded;
        } catch (error) {
            console.error('Decoding error:', error);
            return '';
        }
    },

    // Utility function to check if string is valid base64
    isBase64: function(str) {
        try {
            return btoa(atob(str)) === str;
        } catch (error) {
            return false;
        }
    },

    // Method to validate encoded string
    validateEncoded: function(encoded) {
        if (!encoded || typeof encoded !== 'string') {
            return false;
        }
        const parts = encoded.split('_');
        return parts.length >= 2 && this.isBase64(parts[0].split('').reverse().join(''));
    }
};

// For Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = obfuscator;
}

// For browser environments
if (typeof window !== 'undefined') {
    window.obfuscator = obfuscator;
}
