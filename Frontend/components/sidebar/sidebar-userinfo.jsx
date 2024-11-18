import React from 'react';
import { UserButton } from "@clerk/nextjs"; // Assuming you're using Clerk for authentication

const SidebarUserInfo = () => {
    return (
        <UserButton afterSignOutUrl="/" />
    );
};

export default SidebarUserInfo;
