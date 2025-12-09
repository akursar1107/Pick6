import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

interface ImportDataButtonProps {
  onClick: () => void;
}

export function ImportDataButton({ onClick }: ImportDataButtonProps) {
  return (
    <Button onClick={onClick} variant="default" className="gap-2">
      <Download className="h-4 w-4" />
      Import Data
    </Button>
  );
}
