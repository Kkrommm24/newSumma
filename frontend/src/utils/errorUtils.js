export const errorMap = {
    // Lỗi Unique
    'error_username_exists': 'Tên đăng nhập này đã được sử dụng.',
    'error_email_exists': 'Địa chỉ email này đã được sử dụng.',
    // Lỗi mật khẩu
    'error_password_incorrect': 'Mật khẩu không đúng.',
    'error_old_password_incorrect': 'Mật khẩu cũ không đúng.',
    'password_mismatch': 'Mật khẩu xác nhận không khớp.',
    'password_too_short': 'Mật khẩu phải chứa ít nhất 8 ký tự.',
    'password_too_common': 'Mật khẩu này quá phổ biến.',
    'password_entirely_numeric': 'Mật khẩu không được hoàn toàn là chữ số.',
    'password_too_similar': 'Mật khẩu quá giống với các thông tin cá nhân khác.',
};

export const getErrorMessage = (error, customErrorMap = errorMap) => {
    const genericError = 'Đã xảy ra lỗi không mong muốn.';
    if (error.response?.data) {
        const data = error.response.data;

        // Xử lý trường hợp lỗi đơn giản { "error": "error_code" }
        if (data.error && customErrorMap[data.error]) {
            return customErrorMap[data.error];
        }

        // Xử lý lỗi từ DRF
        if (typeof data === 'object' && !Array.isArray(data)) {
            const errorMessages = [];
            Object.values(data).forEach(errorArray => {
                if (Array.isArray(errorArray)) {
                    errorArray.forEach(msg => {
                        errorMessages.push(customErrorMap[msg] || msg);
                    });
                }
            });
            if (errorMessages.length > 0) return errorMessages.join(' ');
        }
        // Các trường hợp lỗi khác
        if (data.detail) return data.detail;
        if (data.error) return data.error;
    }
    return genericError;
}; 