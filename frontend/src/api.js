import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000"; // Địa chỉ backend Django

export const fetchHelloWorld = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/hello`);
        return response.data.message;
    } catch (error) {
        console.error("Error fetching data:", error);
        return null;
    }
};
