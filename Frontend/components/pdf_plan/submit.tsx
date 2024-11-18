import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useState, useEffect } from "react"
import { useToast } from "@/components/ui/use-toast";

interface SubmitPopupProps {
  onSubmit: (name: string) => void
  onCancel: () => void
  isOpen: boolean
  closeDialog: () => void
  defaultName?: string  
}

export function SubmitPopup({ onSubmit, onCancel, isOpen, closeDialog, defaultName = "" }: SubmitPopupProps) {
  const [name, setName] = useState(defaultName)
  const { toast } = useToast();

  useEffect(() => {
    setName(defaultName); // Set the default name when the dialog opens
  }, [defaultName, isOpen]);

  const handleSave = () => {
    if (name) {
      onSubmit(name)
      closeDialog()
    } else {
      toast({
        variant: "destructive",
        title: "Please provide a name for the symbol",
        description: "",
      });
    }
  }
  const handleCancel = () => {
    onCancel()
    setName(defaultName)  // Reset to default name
    closeDialog()
  }

  return (
    <Dialog open={isOpen} onOpenChange={closeDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Enter a name for the selected symbol.</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input 
              id="name" 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              className="col-span-3" 
              placeholder="Enter name"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>Cancel</Button>
          <Button type="button" onClick={handleSave}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
