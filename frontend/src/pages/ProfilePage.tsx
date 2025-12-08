import { useAuthStore } from "@/stores/authStore";

export default function ProfilePage() {
  const { user } = useAuthStore();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Profile</h1>
      {user ? (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground">Username</p>
            <p className="text-lg font-medium">{user.username}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Email</p>
            <p className="text-lg font-medium">{user.email}</p>
          </div>
          <div className="mt-8">
            <p>TODO: Add profile settings and statistics</p>
          </div>
        </div>
      ) : (
        <p>Please log in to view your profile</p>
      )}
    </div>
  );
}
