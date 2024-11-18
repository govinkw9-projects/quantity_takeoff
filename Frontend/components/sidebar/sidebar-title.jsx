"use client";

import React, { useState } from 'react';
import { Box, Typography } from '@mui/material';
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { ToastAction } from "@/components/ui/toast";
import { useAudioStore } from '@/store/useAudioStore';  


const SidebarTitle = () => {
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();
    const setAudioFiles = useAudioStore((state) => state.setAudioFiles);

    const handleSync = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/syncaudio?days=1'); 
            if (!response.ok) {
                throw new Error('Failed to sync audio files');
            }
    
            const data = await response.json(); 
            setAudioFiles(data.files);   

            toast({
                title: "Sync Successful",
                description: data.message,
                action: (
                    <ToastAction altText="Done">Done</ToastAction>
                ),
            });
        } catch (error) {
            toast({
                variant: "destructive",
                title: "Sync Failed",
                description: "An error occurred while syncing audio files.",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center">
            <Box sx={{ padding: 2 }}>
                <Typography variant="h6">Audio Files</Typography>
                <Button 
                    className="w-full justify-center" 
                    onClick={handleSync} 
                    disabled={loading}
                >
                    {loading ? 'Syncing...' : 'Sync'}
                </Button>
            </Box>
        </div>
    );
};

export default SidebarTitle;
