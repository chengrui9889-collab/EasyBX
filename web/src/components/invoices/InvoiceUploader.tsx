import { useRef, useState, useCallback } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { cn, formatFileSize } from '@/lib/utils';
import { useInvoiceStore } from '@/stores/invoiceStore';
import type { UploadResponse } from '@/types/invoice';

interface FileWithPreview {
  file: File;
  id: string;
  isValid: boolean;
  errorMsg: string | null;
}

const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'pdf'];
const MAX_FILE_SIZE = 50 * 1024 * 1024;
const MAX_FILE_COUNT = 20;

function validateFile(file: File): { valid: boolean; error: string | null } {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
    return { valid: false, error: '不支持的文件格式' };
  }
  if (file.size > MAX_FILE_SIZE) {
    return { valid: false, error: '文件大小超过 50MB 限制' };
  }
  return { valid: true, error: null };
}

interface InvoiceUploaderProps {
  onUploadComplete: (result: UploadResponse) => void;
}

export function InvoiceUploader({ onUploadComplete }: InvoiceUploaderProps) {
  const [selectedFiles, setSelectedFiles] = useState<FileWithPreview[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const uploading = useInvoiceStore((s) => s.uploading);
  const uploadFiles = useInvoiceStore((s) => s.uploadFiles);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArr = Array.from(files);
    const withPreview: FileWithPreview[] = fileArr.map((file) => {
      const { valid, error } = validateFile(file);
      return {
        file,
        id: crypto.randomUUID(),
        isValid: valid,
        errorMsg: valid ? null : error,
      };
    });

    setSelectedFiles((prev) => {
      const merged = [...prev, ...withPreview];
      if (merged.length > MAX_FILE_COUNT) {
        return merged.slice(0, MAX_FILE_COUNT);
      }
      return merged;
    });
  }, []);

  const removeFile = useCallback((id: string) => {
    setSelectedFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles],
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        addFiles(e.target.files);
        e.target.value = '';
      }
    },
    [addFiles],
  );

  const handleUpload = useCallback(async () => {
    const validFiles = selectedFiles.filter((f) => f.isValid).map((f) => f.file);
    if (validFiles.length === 0) return;

    try {
      const result = await uploadFiles(validFiles);
      setSelectedFiles([]);
      onUploadComplete(result);
    } catch {
      // error handled in store
    }
  }, [selectedFiles, uploadFiles, onUploadComplete]);

  const exceeded = selectedFiles.length > MAX_FILE_COUNT;

  return (
    <div className="mb-6">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
          isDragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100',
        )}
      >
        <Upload className="mb-2 h-8 w-8 text-gray-400" />
        <p className="text-sm text-gray-600">
          拖拽文件到此处，或<span className="text-blue-600">点击选择</span>
        </p>
        <p className="mt-1 text-xs text-gray-400">支持 JPG、PNG、PDF 格式，单文件 ≤ 50MB，最多 20 张</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              已选择 {selectedFiles.length} 个文件
            </span>
            {exceeded && (
              <span className="text-xs text-amber-600">
                已超出数量限制，仅上传前 {MAX_FILE_COUNT} 张
              </span>
            )}
          </div>

          <div className="max-h-48 space-y-1 overflow-y-auto">
            {selectedFiles.map((f) => (
              <div
                key={f.id}
                className={cn(
                  'flex items-center justify-between rounded-md px-3 py-2',
                  f.isValid ? 'bg-gray-50' : 'bg-red-50',
                )}
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText
                    className={cn(
                      'h-4 w-4 flex-shrink-0',
                      f.isValid ? 'text-gray-400' : 'text-red-400',
                    )}
                  />
                  <span
                    className={cn(
                      'truncate text-sm',
                      f.isValid ? 'text-gray-700' : 'text-red-600',
                    )}
                  >
                    {f.file.name}
                  </span>
                  <span className="flex-shrink-0 text-xs text-gray-400">
                    {formatFileSize(f.file.size)}
                  </span>
                  {!f.isValid && f.errorMsg && (
                    <span className="flex-shrink-0 text-xs text-red-500">
                      {f.errorMsg}
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(f.id);
                  }}
                  className="ml-2 flex-shrink-0 rounded p-0.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleUpload();
            }}
            disabled={uploading || selectedFiles.filter((f) => f.isValid).length === 0}
            className={cn(
              'mt-3 inline-flex w-full items-center justify-center rounded-md px-4 py-2.5 text-sm font-medium transition-colors',
              uploading || selectedFiles.filter((f) => f.isValid).length === 0
                ? 'cursor-not-allowed bg-gray-200 text-gray-500'
                : 'bg-blue-600 text-white hover:bg-blue-700',
            )}
          >
            {uploading ? (
              <>
                <svg
                  className="mr-2 h-4 w-4 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                上传中...
              </>
            ) : (
              `上传 ${selectedFiles.filter((f) => f.isValid).length} 个文件`
            )}
          </button>
        </div>
      )}
    </div>
  );
}