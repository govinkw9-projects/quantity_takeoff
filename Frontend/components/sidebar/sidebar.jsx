"use client" 


import React from 'react';
import SidebarTitle from '@/components/sidebar/sidebar-title';
import SidebarMenu from '@/components/sidebar/sidebar-menu';
import SidebarUserInfo from '@/components/sidebar/sidebar-userinfo';
import { ScrollArea } from "/components/ui/scroll-area";

const Sidebar = () => {
    return (
        <div className="flex flex-col h-full border-r shadow-md">
            <div className="py-2 border-b">
                <SidebarTitle /> {/* Top section: Title */}
            </div>
            <div className="flex-grow flex -col space-y-2 py-2">
                <SidebarMenu /> {/* Middle section: Scrollable list */}
            </div>
            <div className="py-2 border-t">
                <SidebarUserInfo /> {/* Bottom section: User info, always at the bottom */}
            </div>
        </div>
    );
};

export default Sidebar;
