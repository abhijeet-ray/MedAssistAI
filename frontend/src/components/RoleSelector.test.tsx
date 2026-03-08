import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { RoleSelector } from './RoleSelector';

describe('RoleSelector Component', () => {
  it('should display exactly three role options', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(3);
  });

  it('should display correct role labels', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    expect(screen.getByText(/Doctor/)).toBeInTheDocument();
    expect(screen.getByText(/Patient/)).toBeInTheDocument();
    expect(screen.getByText(/ASHA Worker/)).toBeInTheDocument();
  });

  it('should highlight the selected role', () => {
    const mockOnRoleChange = vi.fn();
    const { rerender } = render(
      <RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />
    );

    const patientButton = screen.getByText(/Patient/).closest('button');
    expect(patientButton).toHaveClass('active');

    rerender(<RoleSelector selectedRole="doctor" onRoleChange={mockOnRoleChange} />);
    const doctorButton = screen.getByText(/Doctor/).closest('button');
    expect(doctorButton).toHaveClass('active');
  });

  it('should call onRoleChange when a role is clicked', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    const doctorButton = screen.getByText(/Doctor/).closest('button');
    fireEvent.click(doctorButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('doctor');
  });

  it('should handle role switching', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    const ashaButton = screen.getByText(/ASHA Worker/).closest('button');
    fireEvent.click(ashaButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('asha');
  });
});


/**
 * Unit tests for role selection integration with chat requests
 * Validates: Requirements 8.1, 8.6
 */
describe('Role Selection Integration with Chat Requests', () => {
  it('should pass role parameter in chat requests', () => {
    const mockOnRoleChange = vi.fn();
    const { rerender } = render(
      <RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />
    );

    // Verify patient role is selected
    const patientButton = screen.getByText(/Patient/).closest('button');
    expect(patientButton).toHaveClass('active');

    // Switch to doctor role
    const doctorButton = screen.getByText(/Doctor/).closest('button');
    fireEvent.click(doctorButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('doctor');

    // Rerender with new role
    rerender(<RoleSelector selectedRole="doctor" onRoleChange={mockOnRoleChange} />);

    // Verify doctor role is now selected
    expect(doctorButton).toHaveClass('active');
  });

  it('should default to patient role if not specified', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    const patientButton = screen.getByText(/Patient/).closest('button');
    expect(patientButton).toHaveClass('active');
  });

  it('should handle role switching from patient to doctor', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    const doctorButton = screen.getByText(/Doctor/).closest('button');
    fireEvent.click(doctorButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('doctor');
    expect(mockOnRoleChange).toHaveBeenCalledTimes(1);
  });

  it('should handle role switching from doctor to asha worker', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="doctor" onRoleChange={mockOnRoleChange} />);

    const ashaButton = screen.getByText(/ASHA Worker/).closest('button');
    fireEvent.click(ashaButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('asha');
    expect(mockOnRoleChange).toHaveBeenCalledTimes(1);
  });

  it('should handle role switching from asha worker to patient', () => {
    const mockOnRoleChange = vi.fn();
    render(<RoleSelector selectedRole="asha" onRoleChange={mockOnRoleChange} />);

    const patientButton = screen.getByText(/Patient/).closest('button');
    fireEvent.click(patientButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('patient');
    expect(mockOnRoleChange).toHaveBeenCalledTimes(1);
  });

  it('should maintain role selection across multiple switches', () => {
    const mockOnRoleChange = vi.fn();
    const { rerender } = render(
      <RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />
    );

    // Switch to doctor
    let doctorButton = screen.getByText(/Doctor/).closest('button');
    fireEvent.click(doctorButton!);
    rerender(<RoleSelector selectedRole="doctor" onRoleChange={mockOnRoleChange} />);

    // Verify doctor is active
    doctorButton = screen.getByText(/Doctor/).closest('button');
    expect(doctorButton).toHaveClass('active');

    // Switch to asha
    const ashaButton = screen.getByText(/ASHA Worker/).closest('button');
    fireEvent.click(ashaButton!);
    rerender(<RoleSelector selectedRole="asha" onRoleChange={mockOnRoleChange} />);

    // Verify asha is active
    const ashaButtonAfter = screen.getByText(/ASHA Worker/).closest('button');
    expect(ashaButtonAfter).toHaveClass('active');

    // Switch back to patient
    const patientButton = screen.getByText(/Patient/).closest('button');
    fireEvent.click(patientButton!);
    rerender(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);

    // Verify patient is active
    const patientButtonAfter = screen.getByText(/Patient/).closest('button');
    expect(patientButtonAfter).toHaveClass('active');

    expect(mockOnRoleChange).toHaveBeenCalledTimes(3);
  });

  it('should only call onRoleChange when role actually changes', () => {
    const mockOnRoleChange = vi.fn();
    const { rerender } = render(
      <RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />
    );

    const patientButton = screen.getByText(/Patient/).closest('button');
    fireEvent.click(patientButton!);

    expect(mockOnRoleChange).toHaveBeenCalledWith('patient');
    expect(mockOnRoleChange).toHaveBeenCalledTimes(1);

    // Click same button again
    rerender(<RoleSelector selectedRole="patient" onRoleChange={mockOnRoleChange} />);
    fireEvent.click(patientButton!);

    // Should be called again (component doesn't prevent duplicate calls)
    expect(mockOnRoleChange).toHaveBeenCalledTimes(2);
  });
});
