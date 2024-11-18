import AWS from 'aws-sdk';
import fs from 'fs';
import path from 'path';
import {Configuration} from "@/lib/config"; 

const s3 = new AWS.S3({
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    region: process.env.AWS_REGION,
});

interface SaveFileResult {
    fileName: string;
    filePath: string;
}


/**
 * Sanitizes a file name by replacing or removing invalid characters.
 * @param fileName - The original file name.
 * @returns A sanitized file name.
 */
const sanitizeFileName = (fileName: string): string => {
    // Replace invalid characters with underscores or remove them
    return fileName.replace(/[:<>|"*?]/g, '_');
};


/**
 * Downloads a file from an S3 bucket and saves it locally.
 * @param key - The key (path) of the object within the bucket.
 * @returns A promise that resolves to an object containing the file name and path.
 */
export const saveFileFromS3 = async (key: string): Promise<SaveFileResult> => {
    try {
        const params: AWS.S3.GetObjectRequest = {
            Bucket: Configuration.S3_BUCKET_NAME,
            Key: key,
        };

        const data = await s3.getObject(params).promise();
        
        if (!data.Body) {
            throw new Error('No data found in the S3 object.');
        }
        
        const fileName = sanitizeFileName(path.basename(key)); 
        const localDir = path.join(".", Configuration.localAudioLocation);
        const filePath = path.join(localDir, fileName);

        fs.mkdirSync(localDir, { recursive: true });

        fs.writeFileSync(filePath, data.Body as Buffer);
        
        console.log(`File saved at: ${filePath}`);
        
        return {
            fileName,
            filePath,
        };
    } catch (error) {
        console.error('Error saving file from S3:', error);
        throw error;
    }
};

/**
 * Downloads all files uploaded in the past specified number of days.
 * @param days - The number of days to look back. If -1, downloads all files.
 * @returns A promise that resolves to an array of objects containing the file names and paths.
 */
export const downloadLatestFilesFromS3 = async (days: number): Promise<SaveFileResult[]> => {
    try {
        const params: AWS.S3.ListObjectsV2Request = {
            Bucket: Configuration.S3_BUCKET_NAME,
        };

        const data = await s3.listObjectsV2(params).promise();
        if (!data.Contents) {
            console.log('No files found in the bucket.');
            return [];
        }

        const now = new Date();
        const filteredFiles = data.Contents.filter((item) => {
            if (!item.LastModified) return false;
            const timeDifference = now.getTime() - item.LastModified.getTime();
            const daysDifference = timeDifference / (1000 * 60 * 60 * 24);
            return days === -1 || daysDifference <= days;
        });

        const downloadPromises = filteredFiles.map((file) => saveFileFromS3(file.Key as string));
        const downloadedFiles = await Promise.all(downloadPromises);

        return downloadedFiles;
    } catch (error) {
        console.error('Error downloading latest files:', error);
        throw error;
    }
};
