type Nullable<T> = T | null;

declare module "*.jpeg" {
    const value: any;
    export = value;
}