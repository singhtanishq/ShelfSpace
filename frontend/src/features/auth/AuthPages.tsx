import { useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Library, CheckCircle2, Mail } from "lucide-react";
import { authApi } from "@/api/endpoints";
import { useAuthStore } from "@/stores/auth";
import { apiErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Input, Field } from "@/components/ui/Input";

function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center bg-brand-50/60 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link to="/" className="inline-flex items-center gap-2">
            <Library className="h-8 w-8 text-brand-700" aria-hidden />
            <span className="font-serif text-2xl font-bold text-brand-800">ShelfSpace</span>
          </Link>
          <h1 className="mt-6 font-serif text-2xl font-bold text-brand-950">{title}</h1>
          <p className="mt-1.5 text-sm text-brand-400">{subtitle}</p>
        </div>
        <div className="rounded-2xl border border-brand-100 bg-white p-6 shadow-card sm:p-8">{children}</div>
      </div>
    </div>
  );
}

const loginSchema = z.object({
  identifier: z.string().min(3, "Enter your email or username"),
  password: z.string().min(1, "Enter your password"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setSession = useAuthStore((s) => s.setSession);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<{ identifier: string; password: string }>({ resolver: zodResolver(loginSchema) });

  const onSubmit = handleSubmit(async (data) => {
    try {
      const resp = await authApi.login(data);
      setSession(resp.data.user, resp.data.access_token, resp.data.refresh_token);
      toast.success(`Welcome back, ${resp.data.user.full_name.split(" ")[0]}!`);
      const from = (location.state as any)?.from;
      navigate(from ?? (resp.data.user.role === "admin" ? "/admin" : "/"), { replace: true });
    } catch (err) {
      toast.error(apiErrorMessage(err, "Could not sign you in."));
    }
  });

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to continue to your account">
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Email or username" error={errors.identifier?.message} required>
          <Input {...register("identifier")} autoComplete="username" placeholder="you@example.com" />
        </Field>
        <Field label="Password" error={errors.password?.message} required>
          <Input {...register("password")} type="password" autoComplete="current-password" placeholder="••••••••" />
        </Field>
        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-xs font-medium text-brand-600 hover:text-brand-800">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
          Sign in
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-brand-400">
        New to ShelfSpace?{" "}
        <Link to="/register" className="font-medium text-brand-700 hover:underline">
          Create an account
        </Link>
      </p>
    </AuthShell>
  );
}

const registerSchema = z.object({
  full_name: z.string().min(2, "Enter your full name"),
  username: z.string().regex(/^[a-zA-Z0-9_.]{3,30}$/, "3–30 letters, digits, dots or underscores"),
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(8, "At least 8 characters").max(128),
});

export function RegisterPage() {
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof registerSchema>>({ resolver: zodResolver(registerSchema) });

  const onSubmit = handleSubmit(async (data) => {
    try {
      const resp = await authApi.register(data);
      const url = resp.data.verification_url;
      if (url) {
        toast.success("Account created! Opening verification link (email delivery is disabled in dev).");
        setTimeout(() => window.location.href = url, 1200);
      } else {
        toast.success("Account created! Check your email to verify your address.");
        navigate("/login");
      }
    } catch (err) {
      toast.error(apiErrorMessage(err, "Could not create your account."));
    }
  });

  return (
    <AuthShell title="Create your account" subtitle="Join thousands of readers on ShelfSpace">
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Field label="Full name" error={errors.full_name?.message} required>
          <Input {...register("full_name")} autoComplete="name" placeholder="Jane Reader" />
        </Field>
        <Field label="Username" error={errors.username?.message} required>
          <Input {...register("username")} autoComplete="username" placeholder="jane_reader" />
        </Field>
        <Field label="Email" error={errors.email?.message} required>
          <Input {...register("email")} type="email" autoComplete="email" placeholder="you@example.com" />
        </Field>
        <Field label="Password" error={errors.password?.message} hint="Minimum 8 characters" required>
          <Input {...register("password")} type="password" autoComplete="new-password" placeholder="••••••••" />
        </Field>
        <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
          Create account
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-brand-400">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Reset your password" subtitle="We'll email you a secure reset link">
      {sent ? (
        <div className="flex flex-col items-center gap-3 py-6 text-center">
          <Mail className="h-10 w-10 text-emerald-500" aria-hidden />
          <p className="text-sm text-brand-600">
            If an account exists for <strong>{email}</strong>, a reset link is on its way. The link expires in one hour.
          </p>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Email address" required>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" />
          </Field>
          <Button type="submit" className="w-full" size="lg" loading={busy}>
            Send reset link
          </Button>
        </form>
      )}
      <p className="mt-6 text-center text-sm text-brand-400">
        Remembered it?{" "}
        <Link to="/login" className="font-medium text-brand-700 hover:underline">
          Back to sign in
        </Link>
      </p>
    </AuthShell>
  );
}

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      toast.error("Passwords do not match");
      return;
    }
    setBusy(true);
    try {
      await authApi.resetPassword({ token, new_password: password });
      toast.success("Password reset! You can sign in now.");
      navigate("/login");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Choose a new password" subtitle="Make it strong and unique">
      {!token ? (
        <p className="text-center text-sm text-red-600">This link is missing its token. Request a new reset link.</p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="New password" required hint="Minimum 8 characters">
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </Field>
          <Field label="Confirm password" required>
            <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
          </Field>
          <Button type="submit" className="w-full" size="lg" loading={busy}>
            Reset password
          </Button>
        </form>
      )}
    </AuthShell>
  );
}

export function VerifyEmailPage() {
  const { token: _tokenParam } = useParams();
  const [params] = useSearchParams();
  const token = params.get("token") ?? _tokenParam ?? "";
  const [state, setState] = useState<"pending" | "ok" | "error">("pending");
  const [message, setMessage] = useState("");

  useState(() => {
    if (!token) {
      setState("error");
      setMessage("This link is missing its verification token.");
      return;
    }
    authApi
      .verifyEmail(token)
      .then(() => setState("ok"))
      .catch((err) => {
        setState("error");
        setMessage(apiErrorMessage(err));
      });
  });

  return (
    <AuthShell title="Email verification" subtitle="One quick check and you're all set">
      {state === "pending" && <p className="text-center text-sm text-brand-500">Verifying…</p>}
      {state === "ok" && (
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <CheckCircle2 className="h-12 w-12 text-emerald-500" aria-hidden />
          <p className="text-sm font-medium text-brand-800">Your email has been verified!</p>
          <Button onClick={() => (window.location.href = "/login")}>Continue to sign in</Button>
        </div>
      )}
      {state === "error" && (
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <p className="text-sm text-red-600">{message}</p>
          <Button variant="outline" onClick={() => (window.location.href = "/login")}>
            Back to sign in
          </Button>
        </div>
      )}
    </AuthShell>
  );
}
