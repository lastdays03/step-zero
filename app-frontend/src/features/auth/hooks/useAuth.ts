
import { useAuth as useAuthContext } from '@/providers/AuthProvider';

export const useAuth = () => {
    const { loginWithCredentials } = useAuthContext();

    const login = async (username: string, password: string) => {
        await loginWithCredentials(username, password);
    };

    return { login, loginWithCredentials };
};
