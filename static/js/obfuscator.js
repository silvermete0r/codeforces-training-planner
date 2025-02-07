const obfuscator = {
    encode: function(code) {
        return btoa(unescape(encodeURIComponent(code)));
    },
    decode: function(encoded) {
        return decodeURIComponent(escape(atob(encoded)));
    }
};

module.exports = obfuscator;
