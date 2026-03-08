import React from 'react';
import type { Role } from './RoleSelector';
import { RoleSelector } from './RoleSelector';

interface LayoutProps {
  selectedRole: Role;
  onRoleChange: (role: Role) => void;
  sessionId: string;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  selectedRole,
  onRoleChange,
  sessionId,
  children,
}) => {
  return (
    <div className="app-container">
      {/* Medical Disclaimer */}
      <div className="disclaimer">
        This AI system provides informational insights only and does not provide medical diagnosis.
        Always consult a licensed healthcare professional.
      </div>

      <div className="main-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <h1 className="app-title">MedAssist AI</h1>
          <RoleSelector selectedRole={selectedRole} onRoleChange={onRoleChange} />
        </aside>

        {/* Main Workspace */}
        <main className="workspace">{children}</main>
      </div>

      {/* Session Info (for development) */}
      <div className="session-info">
        Session: {sessionId} | Role: {selectedRole}
      </div>
    </div>
  );
};
