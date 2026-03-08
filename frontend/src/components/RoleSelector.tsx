import React from 'react';

export type Role = 'doctor' | 'patient' | 'asha';

interface RoleSelectorProps {
  selectedRole: Role;
  onRoleChange: (role: Role) => void;
}

export const RoleSelector: React.FC<RoleSelectorProps> = ({ selectedRole, onRoleChange }) => {
  const roles: { value: Role; label: string; icon: string }[] = [
    { value: 'doctor', label: 'Doctor', icon: '👨‍⚕️' },
    { value: 'patient', label: 'Patient', icon: '🧑' },
    { value: 'asha', label: 'ASHA Worker', icon: '👩‍⚕️' },
  ];

  return (
    <div className="role-selector">
      <h2>Select Your Role</h2>
      <div className="role-options">
        {roles.map((role) => (
          <button
            key={role.value}
            className={`role-button ${selectedRole === role.value ? 'active' : ''}`}
            onClick={() => onRoleChange(role.value)}
          >
            {role.icon} {role.label}
          </button>
        ))}
      </div>
    </div>
  );
};
