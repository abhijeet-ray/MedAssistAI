import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DocumentUpload } from './DocumentUpload';
import * as api from '../utils/api';

// Mock the API module
vi.mock('../utils/api', () => ({
  uploadDocument: vi.fn(),
}));

describe('DocumentUpload Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render upload area with instructions', () => {
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={vi.fn()}
        onUploadError={vi.fn()}
      />
    );

    expect(screen.getByText(/Drag and drop PDF, JPEG, or PNG files here/)).toBeInTheDocument();
    expect(screen.getByText(/or click to browse/)).toBeInTheDocument();
  });

  it('should accept PDF files', async () => {
    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toHaveAttribute('accept', '.pdf,.jpg,.jpeg,.png');
  });

  it('should reject invalid file types', async () => {
    const mockOnUploadError = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={vi.fn()}
        onUploadError={mockOnUploadError}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockOnUploadError).toHaveBeenCalledWith('Please upload a PDF, JPEG, or PNG file');
    });
  });

  it('should show upload progress', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Uploading/)).toBeInTheDocument();
    });
  });

  it('should call API with correct payload', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="doctor"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(api.uploadDocument).toHaveBeenCalledWith('test-session', 'doctor', file);
    });
  });

  it('should call onUploadComplete on successful upload', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(
      () => {
        expect(mockOnUploadComplete).toHaveBeenCalledWith('doc-123');
      },
      { timeout: 3000 }
    );
  });

  it('should handle API errors', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      error: {
        code: 'UPLOAD_ERROR',
        message: 'File size exceeds limit',
        retryable: true,
      },
    });

    const mockOnUploadError = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={vi.fn()}
        onUploadError={mockOnUploadError}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockOnUploadError).toHaveBeenCalledWith('File size exceeds limit');
    });
  });

  it('should display user-friendly error messages', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      error: {
        code: 'UPLOAD_ERROR',
        message: 'Unable to upload document. Please check your file format and try again.',
        retryable: true,
      },
    });

    const mockOnUploadError = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={vi.fn()}
        onUploadError={mockOnUploadError}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockOnUploadError).toHaveBeenCalledWith(
        'Unable to upload document. Please check your file format and try again.'
      );
    });
  });

  it('should handle drag and drop', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const uploadArea = screen.getByText(/Drag and drop/).closest('div');
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

    fireEvent.dragOver(uploadArea!);
    fireEvent.drop(uploadArea!, { dataTransfer: { files: [file] } });

    await waitFor(
      () => {
        expect(mockOnUploadComplete).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });

  it('should accept JPEG files', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(
      () => {
        expect(mockOnUploadComplete).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });

  it('should accept PNG files', async () => {
    vi.mocked(api.uploadDocument).mockResolvedValue({
      data: { documentId: 'doc-123', status: 'processing' },
    });

    const mockOnUploadComplete = vi.fn();
    render(
      <DocumentUpload
        sessionId="test-session"
        role="patient"
        onUploadComplete={mockOnUploadComplete}
        onUploadError={vi.fn()}
      />
    );

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'test.png', { type: 'image/png' });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(
      () => {
        expect(mockOnUploadComplete).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });
});
