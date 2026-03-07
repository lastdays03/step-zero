
import { LoginForm } from "@/features/auth";

export default function LoginPage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50 dark:bg-zinc-900">
            <div className="w-full max-w-md space-y-8">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                        Sign in to StepZero
                    </h2>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        Or{" "}
                        <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                            start your 14-day free trial
                        </a>
                    </p>
                </div>
                <LoginForm />
            </div>
        </div>
    );
}
