# Local Maven build, bundle and consumer check (2026-11-08/09, America/New_York)
Project: box1-templates 2bd4c96 render of quarkus-monorepo, name site-gateway, modules gateway, ops, simulator (npm run validate output). Workstation: macOS, openjdk version "21.0.13.0.3" 2026-10-24, Apache Maven 3.10.0 (c43a36b8d67be7e0805, podman machine. No registry push; no cluster access.

## 1. mvn -B -ntp verify (build 1)
[INFO] You have 0 Checkstyle violations.
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.489 s -- in org.box1.gateway.InfoResourceTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.005 s -- in org.box1.gateway.ModuleInfoTest
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] You have 0 Checkstyle violations.
[INFO] BugInstance size is 0
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.912 s -- in org.box1.ops.InfoResourceTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.005 s -- in org.box1.ops.ModuleInfoTest
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] You have 0 Checkstyle violations.
[INFO] BugInstance size is 0
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.913 s -- in org.box1.simulator.InfoResourceTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.006 s -- in org.box1.simulator.ModuleInfoTest
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] You have 0 Checkstyle violations.
[INFO] BugInstance size is 0
[INFO] Reactor Summary for site-gateway 1.0.0-SNAPSHOT:
[INFO] site-gateway ....................................... SUCCESS [  0.674 s]
[INFO] gateway ............................................ SUCCESS [  9.484 s]
[INFO] ops ................................................ SUCCESS [  5.575 s]
[INFO] simulator .......................................... SUCCESS [  5.772 s]
[INFO] BUILD SUCCESS
real	0m23.807s

## 2. A failing ops test (assertEquals("not-ops", ...)) fails the build; simulator is skipped, so nothing would be packaged or pushed
[ERROR] Tests run: 2, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.011 s <<< FAILURE! -- in org.box1.ops.ModuleInfoTest
[ERROR] Tests run: 4, Failures: 1, Errors: 0, Skipped: 0
[INFO] Reactor Summary for site-gateway 1.0.0-SNAPSHOT:
[INFO] simulator .......................................... SKIPPED
[INFO] site-gateway ....................................... SUCCESS [  0.881 s]
[INFO] gateway ............................................ SUCCESS [  7.575 s]
[ERROR] ops ................................................ FAILURE [  3.745 s]
[ERROR] BUILD FAILURE

## 3. Bundle digest from two independent builds (box1-maven-bundle functions via evidence/scripts/bundle-local.py, revision aaaa...)
build 1: modules gateway,ops,simulator digest sha256:3037ddca114b081c9fab93b53544af72cf4939e17fb04126e764d8b9204a4639 
build 2: modules gateway,ops,simulator digest sha256:3037ddca114b081c9fab93b53544af72cf4939e17fb04126e764d8b9204a4639 

## 4. skopeo inspect oci:<layout>:latest (registry.access.redhat.com/ubi9/skopeo@sha256:fd3d5c37..., skopeo 1.22.2)
{
    "Digest": "sha256:3037ddca114b081c9fab93b53544af72cf4939e17fb04126e764d8b9204a4639",
    "RepoTags": [],
    "Created": null,
    "DockerVersion": "",
    "Labels": {
        "org.box1.bundle.layout": "/\u003cmodule\u003e/quarkus-app/",
        "org.box1.bundle.modules": "gateway,ops,simulator",
        "org.opencontainers.image.revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "org.opencontainers.image.source": "https://github.com/box1-org/site-gateway",
        "org.opencontainers.image.title": "site-gateway module bundle"
    },
    "Architecture": "amd64",
    "Os": "linux",
    "Layers": [
        "sha256:bd1e074f158902afcb39e06a4804ec20a74ca8cdc4d0a88abda77c22a38275e1"
    ],
    "LayersData": [
        {
            "MIMEType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "Digest": "sha256:bd1e074f158902afcb39e06a4804ec20a74ca8cdc4d0a88abda77c22a38275e1",
            "Size": 50290186,
            "Annotations": null
        }
    ],
    "Env": null
}

## 5. Non-root skopeo copy --retry-times 3 --preserve-digests --digestfile (to a local oci: target, user 1001:0)
digestfile: sha256:3037ddca114b081c9fab93b53544af72cf4939e17fb04126e764d8b9204a4639

## 6. Layer contents (top two levels)
.
./SHA256SUMS
./gateway
./gateway/quarkus-app
./gateway/quarkus-app/app
./gateway/quarkus-app/lib
./gateway/quarkus-app/quarkus
./gateway/quarkus-app/quarkus-app-dependencies.txt
./gateway/quarkus-app/quarkus-run.jar
./ops
./ops/quarkus-app
./ops/quarkus-app/app
./ops/quarkus-app/lib
./ops/quarkus-app/quarkus
./ops/quarkus-app/quarkus-app-dependencies.txt
./ops/quarkus-app/quarkus-run.jar
./simulator
./simulator/quarkus-app
./simulator/quarkus-app/app
./simulator/quarkus-app/lib
./simulator/quarkus-app/quarkus
./simulator/quarkus-app/quarkus-app-dependencies.txt
./simulator/quarkus-app/quarkus-run.jar

## 7. Consumer check: podman load of the layout, then a Containerfile
FROM registry.access.redhat.com/ubi9/openjdk-21-runtime@sha256:cfa544effa28c5c57197a4c9d460812e70efc0965e6f518e1c2e787ff3cb9335
COPY --from=localhost/latest@sha256:3037ddca114b081c9fab93b53544af72cf4939e17fb04126e764d8b9204a4639 / /deployments/site-gateway/
Run: ls /deployments/site-gateway -> SHA256SUMS gateway ops simulator; sha256sum -c SHA256SUMS -> ok;
java -jar /deployments/site-gateway/gateway/quarkus-app/quarkus-run.jar; curl /api/info -> {"repository":"site-gateway","module":"gateway","javaVersion":21}; /q/health/ready -> status UP
