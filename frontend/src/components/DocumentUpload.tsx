import React, { useRef, useState } from 'react';
import { uploadDocument } from '../utils/api';
import type { Role } from './RoleSelector';

interface DocumentUploadProps {
  sessionId: string;
  role: Role;
  onUploadComplete?: (documentId: string) => void;
  onUploadError?: (error: string) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  sessionId,
  role,
  onUploadComplete,
  onUploadError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];

    if (!validTypes.includes(file.type)) {
      onUploadError?.('Please upload a PDF, JPEG, or PNG file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 90, 90));
      }, 100);

      // Call API to upload document
      const result = await uploadDocument(sessionId, role, file);

      clearInterval(progressInterval);

      if (result.error) {
        onUploadError?.(result.error.message);
        setIsUploading(false);
        setUploadProgress(0);
        return;
      }

      if (result.data?.documentId) {
        setUploadProgress(100);
        onUploadComplete?.(result.data.documentId);

        // Reset
        setTimeout(() => {
          setIsUploading(false);
          setUploadProgress(0);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        }, 500);
      }
    } catch (error) {
      onUploadError?.(
        error instanceof Error ? error.message : 'Upload failed. Please try again.'
      );
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--accent-primary)';
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.currentTarget.style.borderColor = 'var(--border-glass)';
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--border-glass)';
    handleFileSelect(e.dataTransfer.files);
  };

  return (
    <div
      className="upload-area"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      style={{ cursor: isUploading ? 'not-allowed' : 'pointer', opacity: isUploading ? 0.6 : 1 }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={(e) => handleFileSelect(e.target.files)}
        style={{ display: 'none' }}
        disabled={isUploading}
      />
      {isUploading ? (
        <>
          <p>📤 Uploading... {uploadProgress}%</p>
          <div
            style={{
              width: '100%',
              height: '4px',
              background: 'var(--bg-secondary)',
              borderRadius: '2px',
              marginTop: '16px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${uploadProgress}%`,
                height: '100%',
                background: 'var(--accent-primary)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </>
      ) : (
        <>
          <p>📄 Drag and drop PDF, JPEG, or PNG files here</p>
          <p className="upload-hint">or click to browse</p>
        </>
      )}
    </div>
  );
};
